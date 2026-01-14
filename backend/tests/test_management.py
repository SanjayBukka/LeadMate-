import pytest
from management.repo_analyzer import RepoAnalyzer
import os
import shutil

@pytest.fixture
def temp_repo(tmp_path):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    # Initialize a dummy git repo
    import git
    repo = git.Repo.init(repo_dir)
    test_file = repo_dir / "test.py"
    test_file.write_text("print('hello')")
    repo.index.add(["test.py"])
    repo.index.commit("Initial commit")
    return str(repo_dir)

def test_repo_analyzer_init(temp_repo):
    analyzer = RepoAnalyzer(temp_repo)
    assert analyzer.repo_path == temp_repo
    assert analyzer.repo is None

def test_repo_analyzer_open(temp_repo):
    analyzer = RepoAnalyzer(temp_repo)
    assert analyzer.clone_or_open_repo("") is True
    assert analyzer.repo is not None

def test_get_commits_data(temp_repo):
    analyzer = RepoAnalyzer(temp_repo)
    analyzer.clone_or_open_repo("")
    df = analyzer.get_commits_data()
    assert not df.empty
    assert len(df) == 1
    assert df.iloc[0]['message'] == "Initial commit"

def test_get_file_analysis(temp_repo):
    analyzer = RepoAnalyzer(temp_repo)
    analyzer.clone_or_open_repo("")
    analysis = analyzer.get_file_analysis()
    assert ".py" in analysis
    assert analysis[".py"] == 1
