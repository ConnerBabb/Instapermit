from unittest.mock import patch

from main import main


class TestMainCLI:
    """Tests for CLI argument parsing and main() orchestration."""

    @patch("main.enhance_products")
    @patch("main.scrape_products", return_value=[])
    def test_no_products_exits_early(self, mock_scrape, mock_enhance, capsys):
        """When scraper returns nothing, enhance should not be called."""
        with patch("sys.argv", ["main.py"]):
            main()
        mock_scrape.assert_called_once_with(query="laptops", max_products=5)
        mock_enhance.assert_not_called()
        assert "No products found" in capsys.readouterr().out

    @patch("main.enhance_products")
    @patch("main.scrape_products", return_value=[])
    def test_default_args(self, mock_scrape, mock_enhance):
        """Default query should be 'laptops' with max 5."""
        with patch("sys.argv", ["main.py"]):
            main()
        mock_scrape.assert_called_once_with(query="laptops", max_products=5)

    @patch("main.enhance_products")
    @patch("main.scrape_products", return_value=[])
    def test_custom_query(self, mock_scrape, mock_enhance):
        with patch("sys.argv", ["main.py", "--query=headphones"]):
            main()
        mock_scrape.assert_called_once_with(query="headphones", max_products=5)

    @patch("main.enhance_products")
    @patch("main.scrape_products", return_value=[])
    def test_custom_max(self, mock_scrape, mock_enhance):
        with patch("sys.argv", ["main.py", "--max=10"]):
            main()
        mock_scrape.assert_called_once_with(query="laptops", max_products=10)

    @patch("main.enhance_products", side_effect=lambda p: p)
    @patch("main.scrape_products")
    def test_full_pipeline(self, mock_scrape, mock_enhance, sample_products, capsys):
        """When products are found, both raw and enhanced data should be printed."""
        mock_scrape.return_value = sample_products
        with patch("sys.argv", ["main.py"]):
            main()
        mock_scrape.assert_called_once()
        mock_enhance.assert_called_once_with(sample_products)
        output = capsys.readouterr().out
        assert "RAW SCRAPED DATA" in output
        assert "ENHANCED DATA" in output
