import time

from celery import shared_task
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .evidence import collect_evidence
from .media import extract_frames, image_url
from .models import CoachingTurn, MediaAsset
from .provider import MEDIA_PROMPT, ProviderError, coach, remote_json
from .schemas import validate_plan


def authorized(owner):
    return (
        owner.is_active
        and owner.verification == "approved"
        and (settings.AI_PROVIDER == "demo" or owner.ai_consent)
    )


@shared_task
def process_media(asset_id):
    with transaction.atomic():
        asset = (
            MediaAsset.objects.select_for_update()
            .filter(pk=asset_id, state="queued")
            .select_related("owner")
            .first()
        )
        if not asset:
            return
        asset.state = "processing"
        asset.save(update_fields=["state"])
    try:
        if not authorized(asset.owner):
            raise ProviderError("账号状态或模型处理授权已失效。")
        frames = (
            [{"frame": 0, "seconds": 0, "image": asset.file.read()}]
            if asset.kind == "image"
            else extract_frames(asset.file.path)
        )
        if settings.AI_PROVIDER == "demo":
            observation = {
                "observations": [],
                "limitations": ["离线演示已完成文件校验和抽帧，但未进行视觉推理。"],
                "provider": "demo",
                "frames": [{"frame": x["frame"], "seconds": x["seconds"]} for x in frames],
            }
        elif settings.AI_PROVIDER == "remote":
            content = [
                {"type": "text", "text": f"分析目标：{asset.subject}。以下帧按时间顺序提供。"}
            ]
            for frame in frames:
                content.extend(
                    [
                        {
                            "type": "text",
                            "text": f"frame={frame['frame']}, seconds={frame['seconds']}",
                        },
                        {"type": "image_url", "image_url": {"url": image_url(frame["image"])}},
                    ]
                )
            observation, usage = remote_json(
                [{"role": "system", "content": MEDIA_PROMPT}, {"role": "user", "content": content}]
            )
            if (
                not isinstance(observation, dict)
                or not isinstance(observation.get("observations"), list)
                or not isinstance(observation.get("limitations"), list)
                or not observation["limitations"]
                or len(observation["observations"]) > 8
            ):
                raise ProviderError("视觉分析格式无效，请重试。")
            for item in observation["observations"]:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get("text"), str)
                    or len(item["text"]) > 2000
                    or type(item.get("frame")) is not int
                    or item["frame"] not in range(len(frames))
                    or item.get("confidence") not in {"low", "medium", "high"}
                ):
                    raise ProviderError("视觉分析引用无效，请重试。")
            if (
                any(not isinstance(x, str) or len(x) > 2000 for x in observation["limitations"])
                or len(observation["limitations"]) > 10
            ):
                raise ProviderError("视觉分析局限格式无效。")
            observation.update(
                provider="remote",
                model=settings.AI_MODEL,
                prompt_version="media-v1",
                usage=usage,
                frames=[{"frame": x["frame"], "seconds": x["seconds"]} for x in frames],
            )
        else:
            raise ProviderError("未知模型服务配置。")
        MediaAsset.objects.filter(pk=asset_id).update(
            state="ready", observations=observation, error=""
        )
    except (ProviderError, OSError) as exc:
        MediaAsset.objects.filter(pk=asset_id).update(
            state="failed",
            error=str(exc)[:200] if isinstance(exc, ProviderError) else "文件已删除或不可读取。",
        )
    except Exception:
        MediaAsset.objects.filter(pk=asset_id).update(
            state="failed", error="媒体处理失败，请重试。"
        )


@shared_task
def process_turn(turn_id):
    with transaction.atomic():
        turn = (
            CoachingTurn.objects.select_for_update()
            .filter(pk=turn_id, state="queued")
            .select_related("session__owner")
            .first()
        )
        if not turn:
            return
        turn.state = "processing"
        turn.save(update_fields=["state"])
    start = time.monotonic()
    try:
        if not authorized(turn.session.owner):
            raise ProviderError("账号状态或模型处理授权已失效。")
        evidence, ids = collect_evidence(turn.session.owner_id, turn.media_ids)
        if len(evidence["media"]) != len(turn.media_ids):
            raise ProviderError("选中的媒体已删除或尚未处理完成。")
        history = list(
            reversed(
                list(
                    turn.session.turns.filter(state="ready", id__lt=turn.pk)
                    .order_by("-id")
                    .values("question", "answer")[:6]
                )
            )
        )
        result, usage = coach(turn.question, evidence, ids, history)
        if (
            not isinstance(result, dict)
            or not isinstance(result.get("answer"), str)
            or not 1 <= len(result["answer"]) <= 12000
            or "plan" not in result
        ):
            raise ProviderError("教练回答格式无效，请重试。")
        plan = result["plan"]
        if plan is not None:
            validate_plan(plan, ids)
        CoachingTurn.objects.filter(pk=turn_id).update(
            state="ready",
            answer=result["answer"],
            plan=plan or {},
            evidence_ids=ids,
            provider=settings.AI_PROVIDER,
            model=settings.AI_MODEL if settings.AI_PROVIDER == "remote" else "offline-rules-v1",
            usage=usage,
            latency_ms=int((time.monotonic() - start) * 1000),
            error="",
        )
    except (ProviderError, ValidationError) as exc:
        CoachingTurn.objects.filter(pk=turn_id).update(
            state="failed", error=str(exc)[:200], latency_ms=int((time.monotonic() - start) * 1000)
        )
    except Exception:
        CoachingTurn.objects.filter(pk=turn_id).update(
            state="failed", error="教练生成失败，请稍后重试。"
        )
