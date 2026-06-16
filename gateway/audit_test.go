package main

import (
	"testing"
	"time"
)

func TestEmitAuditEvent(t *testing.T) {
	event := &AuditEvent{
		ID:             "test-id",
		Timestamp:      time.Now(),
		TenantID:       "tenant-123",
		Provider:       "openai",
		Model:          "gpt-4",
		PromptCount:    1,
		RequestSize:    100,
		ResponseStatus: 200,
		DurationMs:     50,
	}

	// Make sure it runs and serializes without errors
	EmitAuditEvent(event)
}
