"""Build the two-arm MuJoCo visualization scene from the packaged YAM asset."""

from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from pathlib import Path

from .yam_kinematics import default_yam_model_path


ARM_MOUNT_Y = {"left": 0.30, "right": -0.30}
ARM_REPLICA = {"right": 0, "left": 1}
HAND_MODEL_PREFIX = {"left": "sim_left/", "right": "sim_right/"}


def default_inspire_hand_model_path(side: str) -> Path:
    if side not in HAND_MODEL_PREFIX:
        raise ValueError(f"unknown hand side: {side!r}")
    return (
        Path(__file__).resolve().parent
        / "assets"
        / "hand_model"
        / f"{side}_hand.urdf"
    )


def build_dual_yam_scene_xml(
    single_arm_path: str | Path | None = None,
) -> str:
    """Return an in-memory MJCF scene containing two replicated YAM arms.

    FK/IK still use two independent six-axis models. The replicated model is
    visualization-only and therefore cannot accidentally introduce coupled IK
    or a twelve-axis hardware command path.
    """

    source = (
        Path(single_arm_path)
        if single_arm_path is not None
        else default_yam_model_path()
    ).resolve()
    root = ET.parse(source).getroot()
    root.set("model", "dual_yam_pro")

    compiler = root.find("compiler")
    if compiler is None:
        raise ValueError("YAM model is missing its compiler element")
    mesh_dir = (source.parent / compiler.get("meshdir", "")).resolve()
    compiler.set("meshdir", str(mesh_dir))
    compiler.set("conflict", "merge")

    asset = root.find("asset")
    if asset is None:
        raise ValueError("YAM model is missing its asset element")
    for side in ("left", "right"):
        ET.SubElement(
            asset,
            "model",
            {
                "name": f"{side}_inspire_hand_model",
                "file": str(default_inspire_hand_model_path(side).resolve()),
            },
        )

    statistic = root.find("statistic")
    if statistic is not None:
        statistic.set("center", "0.38 0 0.30")
        statistic.set("extent", "1.15")

    worldbody = root.find("worldbody")
    if worldbody is None:
        raise ValueError("YAM model is missing its worldbody")
    base = worldbody.find("./body[@name='base']")
    if base is None:
        raise ValueError("YAM model is missing its base body")
    base_index = list(worldbody).index(base)
    worldbody.remove(base)
    base = copy.deepcopy(base)
    base.set("pos", f"0 {ARM_MOUNT_Y['right']} 0")
    replicate = ET.Element(
        "replicate",
        {"count": "2", "offset": "0 0.60 0", "sep": "_"},
    )
    replicate.append(base)
    worldbody.insert(base_index, replicate)

    old_target = worldbody.find("./body[@name='quest_target_body']")
    if old_target is not None:
        worldbody.remove(old_target)
    for side, rgba in (
        ("left", "0.12 0.55 1 0.75"),
        ("right", "1 0.35 0.08 0.75"),
    ):
        body = ET.SubElement(
            worldbody,
            "body",
            {"name": f"{side}_arm_target_body", "mocap": "true", "pos": "0 0 -10"},
        )
        ET.SubElement(
            body,
            "site",
            {
                "name": f"{side}_arm_target",
                "type": "sphere",
                "size": "0.014",
                "rgba": rgba,
            },
        )

    # Each physical hand is a mocap-rooted attached URDF model. Its root follows
    # the achieved YAM TCP, while the existing translucent skeleton remains the
    # Quest target. Rx(+90°) aligns the hand's -Y finger direction with TCP -Z;
    # the following local Ry(180°) flip keeps that direction while putting the
    # palm side (-hand X in this URDF) toward the table.
    for side in ("left", "right"):
        mount = ET.SubElement(
            worldbody,
            "body",
            {
                "name": f"{side}_inspire_hand_mount",
                "mocap": "true",
                "pos": "0 0 -10",
            },
        )
        alignment = ET.SubElement(
            mount,
            "body",
            {
                "name": f"{side}_inspire_hand_alignment",
                "quat": "0 0 0.7071067812 0.7071067812",
            },
        )
        ET.SubElement(
            alignment,
            "attach",
            {
                "model": f"{side}_inspire_hand_model",
                "body": (
                    "L_hand_base_link" if side == "left" else "R_hand_base_link"
                ),
                "prefix": HAND_MODEL_PREFIX[side],
            },
        )

    table = worldbody.find("./geom[@name='white_table_top']")
    if table is not None:
        table.set("size", "0.60 0.62 0.035")
        table.set("pos", "0.55 0 -0.035")

    camera = worldbody.find("./camera[@name='fixed_table_view']")
    if camera is not None:
        camera.set("name", "ego_reference_camera")
        camera.set("pos", "-0.44 0 0.50")
        camera.set("fovy", "58")
        camera.set("target", "table_focus")
    table_focus = worldbody.find("./body[@name='table_focus']")
    if table_focus is not None:
        table_focus.set("pos", "0.35 0 0.18")

    return ET.tostring(root, encoding="unicode")


def dual_joint_names(side: str) -> tuple[str, ...]:
    try:
        replica = ARM_REPLICA[side]
    except KeyError as error:
        raise ValueError(f"unknown arm side: {side!r}") from error
    return tuple(f"joint{index}_{replica}" for index in range(1, 7))


def dual_tcp_site_name(side: str) -> str:
    try:
        replica = ARM_REPLICA[side]
    except KeyError as error:
        raise ValueError(f"unknown arm side: {side!r}") from error
    return f"inspire_tcp_{replica}"


def simulated_hand_joint_name(side: str, urdf_joint_name: str) -> str:
    try:
        prefix = HAND_MODEL_PREFIX[side]
    except KeyError as error:
        raise ValueError(f"unknown hand side: {side!r}") from error
    return f"{prefix}{urdf_joint_name}"
