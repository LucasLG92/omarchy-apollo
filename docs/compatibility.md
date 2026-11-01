# Compatibility: Mi 10T 5G and Mi 10T Pro 5G

**The base is reusable for the regular Mi 10T 5G, but this Omarchy adaptation is not validated on that model.** Physical results published here come from one **Mi 10T Pro** development unit. The current private development images are not a generic download or a direct-flash option for another phone.

## Model matrix

| Model | Official SoC / modem | Official main camera | Official RAM / storage | This project's evidence |
| --- | --- | --- | --- | --- |
| Mi 10T Pro 5G | Snapdragon 865 / X55 | Samsung HMX, 108 MP | 8 GB / 128 or 256 GB | One Pro unit, with the bounded [R9–R19 results](status.md); incomplete phone acceptance |
| Mi 10T 5G, regular model | Snapdragon 865 / X55 | Sony IMX682, 64 MP | 6 or 8 GB / 128 GB | **Not tested by this project**; variant integration and its own hardware acceptance still required |

Hardware specifications in the middle columns are from [Xiaomi's official comparison](https://www.mi.com/uk/mi-10t/specs/). Megapixels identify the hardware; they do not promise native Linux capture at that resolution. The tested Pro driver currently has no 108 MP mode.

The [upstream Apollo package project](https://github.com/royka1/Xiaomi-Apollo-pmOS-packages/tree/4c52c8bc8f8bd23a0e31dcd944a15f838777c3e2) explicitly targets both variants. That shared platform makes source reuse plausible; **upstream family coverage does not validate this Omarchy integration on the non-Pro**.

## What the non-Pro needs

1. Review/adapt and physically validate its **IMX682 main-camera path**, device-tree selection, libcamera configuration and tuning. The current HMX-focused Pro results cannot be transferred to it.
2. Check the actual RAM/storage variant and provision storage for that phone. Fixed filesystem sizes, partition assumptions and boot references from another unit are not a provisioning recipe.
3. Use only that unit's private radio/sensor calibration where required, with reviewed handling and no public export. Never reuse another phone's NV/EFS, private signing material or unit identifiers.
4. Repeat boot/recovery and the full [hardware matrix](status.md) on the regular model. Shared hardware and a successful Pro trial do not establish touch, cameras, telephony, power or recovery acceptance there.

The same per-unit restrictions apply to moving an artifact between two Pro phones. A matching model name or codename is insufficient.

## Can the current private image be shared or flashed directly?

**No.** Development root/boot artifacts depend on the development unit's filesystem UUIDs, capacity/provisioning, private NV/calibration and signing configuration. They are **not redistributable or validated for cross-device flashing**. No actual UUID, private key, NV content or per-device filesystem/boot image is published in this repository.

A future public builder must parameterize the device variant and storage, establish fresh local filesystem/boot references and signing configuration, stage only the receiving phone's own private data, and verify recovery before installation. The current source patches and theme staging tools are not that complete installer.

As of the latest published R19 result, testing was in RAM and **permanent installation was not completed or validated by that trial**.

## Respuesta breve en español

La base puede aprovecharse para el Mi 10T 5G normal, pero **este port solo tiene pruebas físicas en el Pro conectado**. El normal requiere validar/adaptar su cámara principal, RAM/almacenamiento y calibración de su propia unidad. No se debe flashear ni compartir directamente la imagen privada actual, tampoco entre dos Pro. Primero necesita una construcción/configuración específica y pruebas propias. Las fuentes oficiales y la cobertura upstream orientan la adaptación; no demuestran compatibilidad de esta versión.
