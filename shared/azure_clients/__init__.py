"""Azure client wrappers for inter-agent messaging.

Modules:
- openai_client.py          — Azure OpenAI chat completion wrapper
- servicebus_client.py      — Service Bus send/receive helpers
- eventhub_client.py        — Event Hubs producer/consumer helpers (single hub)
- eventhub_pipeline.py      — Event Hubs multi-hub pipeline helper
- eventgrid_client.py       — Event Grid publish helpers (legacy)
- eventgrid_publisher.py    — Event Grid publisher (SRP)
- eventgrid_pipeline.py     — Event Grid + Storage Queue combined pipeline helper
- storage_queue_receiver.py — Storage Queue receiver (SRP)
"""

from azure_clients.eventgrid_client import EventGridPublisher
from azure_clients.eventgrid_pipeline import EventGridPipelineMessaging
from azure_clients.eventgrid_publisher import PipelineEventGridPublisher
from azure_clients.eventhub_client import EventHubConsumer, EventHubProducer
from azure_clients.eventhub_pipeline import EventHubPipelineMessaging
from azure_clients.openai_client import AzureOpenAIClient
from azure_clients.servicebus_client import ServiceBusHelper
from azure_clients.storage_queue_receiver import StorageQueueReceiver

# Convenience alias: PipelineMessaging exposes the same send/receive_one/close
# API that samples expect for Service Bus-based pipelines.
PipelineMessaging = ServiceBusHelper

__all__ = [
    "AzureOpenAIClient",
    "EventGridPipelineMessaging",
    "EventGridPublisher",
    "EventHubConsumer",
    "EventHubPipelineMessaging",
    "EventHubProducer",
    "PipelineEventGridPublisher",
    "PipelineMessaging",
    "ServiceBusHelper",
    "StorageQueueReceiver",
]
