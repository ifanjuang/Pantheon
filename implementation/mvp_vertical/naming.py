"""Strict, portable naming for project documents stored on the NAS."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import PurePosixPath


PHASE_FOLDERS = {
    "GESTION": "00_Gestion",
    "CONCEPTION": "10_Conception",
    "AUTORISATIONS": "20_Autorisations",
    "DCE": "30_DCE",
    "MARCHE": "40_Marche",
    "CHANTIER": "50_Chantier",
    "RECEPTION": "60_Reception",
    "SINISTRES": "90_Sinistres",
}

_PORTABLE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")
_UPPER_TOKEN = re.compile(r"^[A-Z0-9][A-Z0-9-]*$")
_REVISION = re.compile(r"^[A-Z][1-9][0-9]*$")


class DocumentNameError(ValueError):
    """The source path does not conform to the agency document convention."""


@dataclass(frozen=True)
class DocumentName:
    project_code: str
    revision_index: str
    phase_code: str
    phase_folder: str
    distributor: str
    document_type: str
    object_name: str
    document_date: date
    extension: str
    filename: str

    def as_dict(self) -> dict:
        value = asdict(self)
        value["document_date"] = self.document_date.isoformat()
        return value


def parse_document_name(source_ref: str) -> DocumentName:
    """Parse ``Projet_indice_phase_distributeur_type_objet_date.ext``.

    Underscores are structural separators. Compound values therefore use
    hyphens, which keeps the convention reversible on Windows, Linux and NAS
    shares.
    """
    source = PurePosixPath(source_ref)
    filename = source.name
    if not filename or "." not in filename:
        raise DocumentNameError("document filename must include an extension")
    stem, extension = filename.rsplit(".", 1)
    fields = stem.split("_")
    if len(fields) != 7:
        raise DocumentNameError(
            "expected Projet_indice_phase_distributeur_type_objet_date.ext; "
            "use hyphens inside fields"
        )
    project, revision, phase, distributor, document_type, object_name, raw_date = fields

    if not _PORTABLE_TOKEN.fullmatch(project):
        raise DocumentNameError("project must be a portable token; use hyphens, not spaces")
    if not _REVISION.fullmatch(revision):
        raise DocumentNameError("revision index must look like A1, B1 or B2")
    if phase not in PHASE_FOLDERS:
        raise DocumentNameError(f"unknown phase {phase!r}")
    for label, value in (
        ("distributor", distributor),
        ("document type", document_type),
        ("object", object_name),
    ):
        if not _UPPER_TOKEN.fullmatch(value):
            raise DocumentNameError(f"{label} must use uppercase letters, digits and hyphens")
    if not re.fullmatch(r"[A-Za-z0-9]+", extension):
        raise DocumentNameError("extension must be alphanumeric")
    try:
        parsed_date = date.fromisoformat(raw_date)
    except ValueError as exc:
        raise DocumentNameError("date must be a valid YYYY-MM-DD date") from exc

    expected_folder = PHASE_FOLDERS[phase]
    if source.parent.name != expected_folder:
        raise DocumentNameError(
            f"phase {phase} must be stored directly in {expected_folder}, "
            f"not {source.parent.name or '.'}"
        )
    return DocumentName(
        project_code=project,
        revision_index=revision,
        phase_code=phase,
        phase_folder=expected_folder,
        distributor=distributor,
        document_type=document_type,
        object_name=object_name,
        document_date=parsed_date,
        extension=extension.lower(),
        filename=filename,
    )
