import importlib
import sys
from pathlib import Path
import unittest
from unittest.mock import call, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class AppImportTest(unittest.TestCase):
    def test_package_imports_from_repo_root(self):
        module = importlib.import_module("sahAI.backend.app")
        self.assertTrue(hasattr(module, "st"))

    def test_small_talk_response(self):
        module = importlib.import_module("sahAI.backend.app")
        response = module.get_small_talk_response("hi there")
        self.assertIn("hi", response.lower())
        self.assertIn("R25", response)
        self.assertIsNone(
            module.get_small_talk_response("Which attendance rule applies?")
        )

    def test_general_question_stays_outside_regulation_retrieval(self):
        module = importlib.import_module("sahAI.backend.app")
        self.assertFalse(module.is_regulation_question("What is photosynthesis?"))
        self.assertTrue(
            module.is_regulation_question("What attendance is required in R25?")
        )
        self.assertTrue(
            module.is_regulation_question("How many credits are needed to graduate?")
        )

    def test_general_answer_uses_gemini_without_regulation_passages(self):
        from sahAI.backend import llm

        with patch.object(llm, "_get_api_key", return_value="test-key"):
            with patch.object(llm.genai, "Client") as client_factory:
                client = client_factory.return_value
                client.models.generate_content.return_value.text = "Photosynthesis uses light."

                answer = llm.generate_general_answer("What is photosynthesis?")

        self.assertEqual(answer, "Photosynthesis uses light.")
        client.models.generate_content.assert_called_once()

    def test_repo_and_project_dotenv_paths_are_loaded(self):
        module = importlib.import_module("sahAI.backend.app")
        with patch.object(module, "load_dotenv") as load_dotenv:
            module.load_environment()

        self.assertEqual(
            load_dotenv.call_args_list,
            [call(ROOT / ".env"), call(ROOT / "sahAI" / ".env")],
        )

    def test_api_key_can_be_read_from_streamlit_secrets(self):
        from sahAI.backend.llm import _get_api_key

        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            with patch("streamlit.secrets", {"GEMINI_API_KEY": "cloud-test-key"}):
                self.assertEqual(_get_api_key(), "cloud-test-key")


if __name__ == "__main__":
    unittest.main()
