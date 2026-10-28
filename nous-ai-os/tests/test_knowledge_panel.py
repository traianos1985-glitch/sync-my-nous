from executor import knowledge_panel


def test_document_status_is_persisted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    knowledge_panel.set_status("doc.txt", "indexing")
    assert knowledge_panel.statuses()["doc.txt"] == "indexing"
    knowledge_panel.set_status("doc.txt", "indexed")
    assert knowledge_panel.statuses()["doc.txt"] == "indexed"


def test_content_type_and_relevance_filter_search(monkeypatch):
    monkeypatch.setattr(knowledge_panel, "load_json", lambda *_: [{"id": 1, "document_name": "memory.pdf", "text": "SQLite storage durability"}, {"id": 2, "document_name": "notes.txt", "text": "SQLite storage durability"}])
    hits = knowledge_panel.search_documents("SQLite storage durability", "application/pdf", 0.9)
    assert [hit["documentName"] for hit in hits] == ["memory.pdf"]
    assert hits[0]["score"] == 1