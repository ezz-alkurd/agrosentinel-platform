"""Small synthetic regression checks for preparation policy (not source-image QA)."""
import io
import unittest
from prepare_public import Groups, fingerprint, ground_splits, validate_pd
from PIL import Image


class PreparationTests(unittest.TestCase):
    def test_transitive_groups(self):
        groups = Groups(5)
        groups.join(4, 3)
        groups.join(1, 4)
        self.assertEqual(groups.find(3), groups.find(1))
        self.assertNotEqual(groups.find(0), groups.find(1))

    def test_pixel_fingerprint_ignores_file_metadata(self):
        image = Image.new("RGB", (40, 20), "green")
        outputs = []
        for compress in (0, 9):
            stream = io.BytesIO()
            image.save(stream, format="PNG", compress_level=compress)
            outputs.append(fingerprint(stream.getvalue())[0])
        self.assertEqual(outputs[0]["pixel_sha256"], outputs[1]["pixel_sha256"])

    def test_rotated_annotation_reference(self):
        row = {"id": "example", "oriented_width": 200, "oriented_height": 400,
               "exif_orientation": 6, "source_annotations": [{"width": "200", "height": "400",
               "class": "example", "xmin": "0", "ymin": "0", "xmax": "200", "ymax": "400"}]}
        fixes = []
        self.assertIsNone(validate_pd(row, fixes))
        self.assertEqual(row["prepared_boxes"][0]["xyxy"], [0, 0, 1, 1])
        self.assertEqual(fixes[0]["action"], "exif_transpose_image_to_annotation_frame")

    def test_ambiguous_geometry_rejected(self):
        row = {"id": "example", "oriented_width": 200, "oriented_height": 400,
               "exif_orientation": 1, "source_annotations": [{"width": "640", "height": "480"}]}
        self.assertEqual(validate_pd(row, []), "annotation_geometry_requires_visual_review")

    def test_grouped_ground_split_and_class_coverage(self):
        rows = [{"task": "ground_classification", "labels": [label], "leakage_group": f"{label}:{i}"}
                for label in ("a", "b") for i in range(20)]
        rows.append({"task": "ground_detection", "labels": ["leaf"], "leakage_group": "a:0"})
        ground_splits(rows)
        for label in ("a", "b"):
            self.assertEqual({r["split"] for r in rows if r["labels"] == [label]}, {"train", "val", "test"})
        self.assertEqual(len({r["split"] for r in rows if r["leakage_group"] == "a:0"}), 1)


if __name__ == "__main__":
    unittest.main()
