package main

import (
	"net/http"
	"strings"
	"testing"
)

func TestExtractAndNormalizeOpenAI(t *testing.T) {
	jsonBody := `{
		"model": "gpt-4",
		"messages": [
			{"role": "user", "content": "Hello, my email is test@example.com"},
			{"role": "assistant", "content": "How can I help you today?"}
		]
	}`

	req, _ := http.NewRequest("POST", "/v1/chat/completions", strings.NewReader(jsonBody))
	normalized, rebuilder, err := ExtractAndNormalize(req, "openai")
	if err != nil {
		t.Fatalf("Failed to normalize OpenAI request: %v", err)
	}

	if normalized.Model != "gpt-4" {
		t.Errorf("Expected model gpt-4, got %s", normalized.Model)
	}

	if len(normalized.Prompts) != 2 {
		t.Fatalf("Expected 2 prompts, got %d", len(normalized.Prompts))
	}

	if normalized.Prompts[0] != "Hello, my email is test@example.com" {
		t.Errorf("Expected first prompt content, got: %s", normalized.Prompts[0])
	}

	// Rebuild with redacted prompts
	newBodyBytes, err := rebuilder([]string{"Hello, my email is [REDACTED]", "How can I help you today?"})
	if err != nil {
		t.Fatalf("Failed to rebuild OpenAI request: %v", err)
	}

	if !strings.Contains(string(newBodyBytes), "[REDACTED]") {
		t.Errorf("Rebuilt body does not contain redacted content: %s", string(newBodyBytes))
	}
}

func TestExtractAndNormalizeAnthropic(t *testing.T) {
	jsonBody := `{
		"model": "claude-3-opus",
		"system": "You are a helpful assistant.",
		"messages": [
			{"role": "user", "content": "My phone number is 123-456-7890"}
		]
	}`

	req, _ := http.NewRequest("POST", "/v1/messages", strings.NewReader(jsonBody))
	normalized, rebuilder, err := ExtractAndNormalize(req, "anthropic")
	if err != nil {
		t.Fatalf("Failed to normalize Anthropic request: %v", err)
	}

	if normalized.Model != "claude-3-opus" {
		t.Errorf("Expected model claude-3-opus, got %s", normalized.Model)
	}

	// System prompt + 1 message = 2 prompts
	if len(normalized.Prompts) != 2 {
		t.Fatalf("Expected 2 prompts, got %d", len(normalized.Prompts))
	}

	if normalized.Prompts[0] != "You are a helpful assistant." {
		t.Errorf("Expected system prompt, got: %s", normalized.Prompts[0])
	}

	// Rebuild
	newBodyBytes, err := rebuilder([]string{"You are a helpful assistant.", "My phone number is [REDACTED]"})
	if err != nil {
		t.Fatalf("Failed to rebuild Anthropic request: %v", err)
	}

	if !strings.Contains(string(newBodyBytes), "[REDACTED]") {
		t.Errorf("Rebuilt body does not contain redacted content: %s", string(newBodyBytes))
	}
}

func TestExtractAndNormalizeGemini(t *testing.T) {
	jsonBody := `{
		"contents": [
			{
				"role": "user",
				"parts": [
					{"text": "Hello, my phone is 555-123-4567"}
				]
			}
		]
	}`

	req, _ := http.NewRequest("POST", "/v1/models/gemini-1.5-flash:generateContent", strings.NewReader(jsonBody))
	normalized, rebuilder, err := ExtractAndNormalize(req, "gemini")
	if err != nil {
		t.Fatalf("Failed to normalize Gemini request: %v", err)
	}

	if normalized.Model != "gemini-1.5-flash" {
		t.Errorf("Expected model gemini-1.5-flash, got %s", normalized.Model)
	}

	if len(normalized.Prompts) != 1 {
		t.Fatalf("Expected 1 prompt, got %d", len(normalized.Prompts))
	}

	if normalized.Prompts[0] != "Hello, my phone is 555-123-4567" {
		t.Errorf("Expected prompt content, got: %s", normalized.Prompts[0])
	}

	// Rebuild
	newBodyBytes, err := rebuilder([]string{"Hello, my phone is [REDACTED]"})
	if err != nil {
		t.Fatalf("Failed to rebuild Gemini request: %v", err)
	}

	if !strings.Contains(string(newBodyBytes), "[REDACTED]") {
		t.Errorf("Rebuilt body does not contain redacted content: %s", string(newBodyBytes))
	}
}
