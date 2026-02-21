import sys
from loguru import logger
from strands import Agent, tool
from strands.models import BedrockModel
from strands.telemetry.config import StrandsTelemetry
from dotenv import load_dotenv
load_dotenv()



# Configure loguru
# logger.remove()  # Remove default handler
# logger.add(sys.stderr, level="DEBUG")

# Enable strands debug logging
# logger.enable("strands")


# Initialize telemetry with OTLP exporter
telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()
telemetry.setup_meter(
    enable_console_exporter=True,
)       # Setup new meter provider and sets it as global



@tool
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    # This is a mock implementation
    return f"The weather in {location} is sunny and 72°F"


def main():
    # Create a BedrockModel
    bedrock_model = BedrockModel(
        model_id="minimax.minimax-m2.1",
        region_name="us-west-2",
        temperature=0.3,
    )

    # Create an agent with a tool
    agent = Agent(
        model=bedrock_model,
        name="WeatherBot",
        system_prompt="You are a helpful weather assistant. Use the get_weather tool to answer questions about weather.",
        tools=[get_weather],
        callback_handler=None,
    )
    
    # Run the agent with a query
    response = agent("What's the weather in San Francisco?")
    logger.info("testing....")
    logger.info(response)


if __name__ == "__main__":
    main()
