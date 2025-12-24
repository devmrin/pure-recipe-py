import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import tempfile
import yaml
import re
from pure_recipe import *

from recipe_scrapers import scrape_me

class TestRecipeApp(unittest.TestCase):

    @patch('pure_recipe.scrape_me')
    def test_save_recipe_to_markdown(self, mock_scrape_me):
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = "Test Recipe"
        mock_scraper.yields.return_value = "4 servings"
        mock_scraper.total_time.return_value = 30
        mock_scraper.ingredients.return_value = ["1 cup flour", "2 eggs"]
        mock_scraper.instructions_list.return_value = ["Mix ingredients", "Bake for 20 minutes"]
        mock_scrape_me.return_value = mock_scraper

        # Use a real temporary directory for actual file operations
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {"directory": tmpdir, "yield": True, "time": True}
            recipe_url = "http://example.com/recipe"
            file_path = save_recipe_to_markdown(recipe_url, settings)

            self.assertTrue(os.path.exists(file_path))
            # Check filename pattern: test-recipe-XXXX.md where XXXX is 4-digit ID
            filename = os.path.basename(file_path)
            self.assertTrue(re.match(r"test-recipe-\d{4}\.md", filename), 
                           f"Filename {filename} doesn't match expected pattern")
            with open(file_path, "r") as f:
                content = f.read()
                self.assertIn("# Test Recipe", content)  # Clean title without dashes
                self.assertIn("**Serves:** 4 servings", content)
                self.assertIn("**Total Time:** 30 mins", content)
                self.assertIn("- 1 cup flour", content)
                self.assertIn("1. Mix ingredients", content)

    @patch('pure_recipe.scrape_me')
    def test_save_recipe_with_optional_ingredient(self, mock_scrape_me):
        """Test that ingredients with (optional) are not wrapped in additional parentheses."""
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = "Test Recipe"
        mock_scraper.yields.return_value = "4 servings"
        mock_scraper.total_time.return_value = 30
        mock_scraper.ingredients.return_value = [
            "1 cup flour",
            "2 eggs (optional)",
            "1 tsp salt"
        ]
        mock_scraper.instructions_list.return_value = ["Mix ingredients", "Bake for 20 minutes"]
        mock_scrape_me.return_value = mock_scraper

        # Use a real temporary directory for actual file operations
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {"directory": tmpdir, "yield": True, "time": True}
            recipe_url = "http://example.com/recipe"
            file_path = save_recipe_to_markdown(recipe_url, settings)

            self.assertTrue(os.path.exists(file_path))
            with open(file_path, "r") as f:
                content = f.read()
                # Check that optional ingredient is printed correctly without extra parentheses
                self.assertIn("- 2 eggs (optional)", content)
                # Ensure it's not wrapped in additional parentheses
                self.assertNotIn("(2 eggs (optional))", content)
                self.assertNotIn("- (2 eggs (optional))", content)

    @patch('pure_recipe.scrape_me')
    def test_normalize_double_parentheses(self, mock_scrape_me):
        """Test that double parentheses in ingredients are normalized to single parentheses."""
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = "Test Recipe"
        mock_scraper.yields.return_value = "4 servings"
        mock_scraper.total_time.return_value = 30
        mock_scraper.ingredients.return_value = [
            "⅛ tsp turmeric ((optional))",
            "¼ tsp lemon zest ( (optional))",
            "¼ tsp salt ((adjust to taste))",
            "1 cup flour (normal)"
        ]
        mock_scraper.instructions_list.return_value = ["Mix ingredients"]
        mock_scrape_me.return_value = mock_scraper

        # Use a real temporary directory for actual file operations
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {"directory": tmpdir, "yield": True, "time": True}
            recipe_url = "http://example.com/recipe"
            file_path = save_recipe_to_markdown(recipe_url, settings)

            self.assertTrue(os.path.exists(file_path))
            with open(file_path, "r") as f:
                content = f.read()
                # Check that double parentheses are normalized
                self.assertIn("- ⅛ tsp turmeric (optional)", content)
                self.assertIn("- ¼ tsp lemon zest (optional)", content)
                self.assertIn("- ¼ tsp salt (adjust to taste)", content)
                self.assertIn("- 1 cup flour (normal)", content)
                # Ensure double parentheses are not present
                self.assertNotIn("((optional))", content)
                self.assertNotIn("( (optional))", content)
                self.assertNotIn("((adjust to taste))", content)

    @patch('pure_recipe.scrape_me')
    def test_trim_whitespace_in_parentheses(self, mock_scrape_me):
        """Test that whitespace inside parentheses is trimmed."""
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = "Test Recipe"
        mock_scraper.yields.return_value = "4 servings"
        mock_scraper.total_time.return_value = 30
        mock_scraper.ingredients.return_value = [
            "1 tbsp ginger (chopped or minced )",
            "½ tbsp garlic (chopped or minced)",
            "1 cup flour ( normal )"
        ]
        mock_scraper.instructions_list.return_value = ["Mix ingredients"]
        mock_scrape_me.return_value = mock_scraper

        # Use a real temporary directory for actual file operations
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {"directory": tmpdir, "yield": True, "time": True}
            recipe_url = "http://example.com/recipe"
            file_path = save_recipe_to_markdown(recipe_url, settings)

            self.assertTrue(os.path.exists(file_path))
            with open(file_path, "r") as f:
                content = f.read()
                # Check that whitespace is trimmed inside parentheses
                self.assertIn("- 1 tbsp ginger (chopped or minced)", content)
                self.assertIn("- ½ tbsp garlic (chopped or minced)", content)
                self.assertIn("- 1 cup flour (normal)", content)
                # Ensure trailing/leading spaces are not present
                self.assertNotIn("(chopped or minced )", content)
                self.assertNotIn("( normal )", content)

    @patch('builtins.open', new_callable=mock_open, read_data="# Test Recipe\n**Serves:** 4 servings\n**Total Time:** 30 mins\n\n## Ingredients\n- 1 cup flour\n- 2 eggs\n\n## Instructions\n1. Mix ingredients\n2. Bake for 20 minutes")
    @patch('os.path.exists', return_value=True)
    def test_view_recipe(self, mock_exists, mock_open):
        settings = {"directory": tempfile.gettempdir(), "yield": True, "time": True}
        recipe_url = "http://example.com/recipe"
        with patch('inquirer.prompt', return_value={"after_view": "Quit"}):
            view_recipe(recipe_url, settings, prompt_save=False)

    @patch('pure_recipe.scrape_me')
    def test_save_list_of_recipes(self, mock_scrape_me):
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = "Test Recipe"
        mock_scraper.yields.return_value = "4 servings"
        mock_scraper.total_time.return_value = 30
        mock_scraper.ingredients.return_value = ["1 cup flour", "2 eggs"]
        mock_scraper.instructions_list.return_value = ["Mix ingredients", "Bake for 20 minutes"]
        mock_scrape_me.return_value = mock_scraper

        # Use a real temporary directory for actual file operations
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {"directory": tmpdir, "yield": True, "time": True}
            url_file = os.path.join(tmpdir, "urls.txt")
            with open(url_file, "w") as f:
                f.write("http://example.com/recipe1\nhttp://example.com/recipe2")

            save_list_of_recipes(url_file, settings)

            # Check that files were created with correct pattern
            files_created = [f for f in os.listdir(tmpdir) 
                            if f.startswith("test-recipe-") and f.endswith(".md")]
            self.assertEqual(len(files_created), 2, "Expected 2 recipe files to be created")
            
            for filename in files_created:
                # Verify filename pattern: test-recipe-XXXX.md
                self.assertTrue(re.match(r"test-recipe-\d{4}\.md", filename),
                               f"Filename {filename} doesn't match expected pattern")
                file_path = os.path.join(tmpdir, filename)
                with open(file_path, "r") as f:
                    content = f.read()
                    self.assertIn("# Test Recipe", content)  # Clean title without dashes
                    self.assertIn("**Serves:** 4 servings", content)
                    self.assertIn("**Total Time:** 30 mins", content)
                    self.assertIn("- 1 cup flour", content)
                    self.assertIn("1. Mix ingredients", content)

    @patch('os.listdir', return_value=["test-recipe.md"])
    @patch('builtins.open', new_callable=mock_open, read_data="# Test Recipe\n**Serves:** 4 servings\n**Total Time:** 30 mins\n\n## Ingredients\n- 1 cup flour\n- 2 eggs\n\n## Instructions\n1. Mix ingredients\n2. Bake for 20 minutes")
    @patch('os.path.exists', return_value=True)
    def test_browse_recipes(self, mock_exists, mock_open, mock_listdir):
        settings = {"directory": tempfile.gettempdir()}
        with patch('inquirer.prompt', side_effect=[{"recipe": "Test Recipe"}, {"back_to_menu": "Quit"}]):
            browse_recipes(settings)

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False)
    @patch('yaml.safe_load', return_value={"directory": tempfile.gettempdir(), "time": True, "yield": True})
    def test_load_yaml(self, mock_safe_load, mock_exists, mock_makedirs):
        settings = load_yaml()
        self.assertIn("directory", settings)
        self.assertIn("time", settings)
        self.assertIn("yield", settings)

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(operations="view", url="http://example.com/recipe"))
    def test_parse_arguments(self, mock_parse_args):
        args = parse_arguments()
        self.assertEqual(args.operations, "view")
        self.assertEqual(args.url, "http://example.com/recipe")

if __name__ == "__main__":
    unittest.main()
