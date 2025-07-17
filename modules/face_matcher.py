"""Module for matching faces across images using face_recognition."""
from typing import List

import face_recognition


def compare_faces(reference_image: str, candidate_images: List[str]) -> List[str]:
    """Return the subset of candidate_images that match the reference_image."""
    try:
        ref = face_recognition.load_image_file(reference_image)
        ref_encodings = face_recognition.face_encodings(ref)
        if not ref_encodings:
            return []
        ref_encoding = ref_encodings[0]
        matches = []
        for img in candidate_images:
            cand = face_recognition.load_image_file(img)
            cand_enc = face_recognition.face_encodings(cand)
            if not cand_enc:
                continue
            result = face_recognition.compare_faces([ref_encoding], cand_enc[0])
            if result[0]:
                matches.append(img)
        return matches
    except Exception as e:
        print(f"Face matching failed: {e}")
        return []
