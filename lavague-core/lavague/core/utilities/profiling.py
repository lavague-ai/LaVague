import time
import pandas as pd
import matplotlib.pyplot as plt
from functools import wraps
import io
from IPython.display import Image
from itertools import cycle
from contextlib import contextmanager

# stores llm and retriever calls
agent_events = []

# stores total runtime of each step
agent_steps = []


# call before each agent step to group events by steps
def start_new_step():
    global agent_events
    agent_events.append([])


def clear_profiling_data():
    global agent_events, agent_steps
    agent_events = []
    agent_steps = []


@contextmanager
def time_profiler(
    event_name, prompt_size=None, html_size=None, full_step_profiling=False
):
    """
    A context manager to profile the execution time of code blocks.

    Parameters:
    - event_name: The name of the event being profiled.
    - prompt_size: Optional size of the prompt, if applicable.
    - html_size: Optional size of the HTML, if applicable.
    - full_step_profiling: Boolean indicating whether to profile full steps or individual events.
    """
    context = {}
    start_time = time.perf_counter()
    try:
        yield context
    finally:
        end_time = time.perf_counter()
        duration = end_time - start_time

        # create profiling record
        record = {
            "event_name": event_name,
            "start_time": start_time,
            "duration": duration,
            **({"prompt_size": prompt_size} if prompt_size is not None else {}),
            **({"html_size": html_size} if html_size is not None else {}),
            **context,
        }

        # append the record to the appropriate list
        if full_step_profiling:
            agent_steps.append(record)
        else:
            if len(agent_events) == 0:
                start_new_step()
            agent_events[-1].append(record)


class ChartGenerator:
    def __init__(self, agent_events, agent_steps):
        self.agent_events = agent_events
        self.total_step_runtime = agent_steps
        self.step_color = "grey"
        self.event_color_scheme = [
            "#FFB3B3",  # Pastel Red
            "#ADD8E6",  # Pastel Blue
            "#B2D8B2",  # Pastel Green
            "#FFCC99",  # Pastel Orange
            "#D1B3FF",  # Pastel Purple
            "#FFB3DE",  # Pastel Pink
            "#B3FFFF",  # Pastel Cyan
            "#FFFFB3",  # Pastel Yellow
            "#FFB3FF",  # Pastel Magenta
            "#D2B48C",  # Pastel Brown
        ]

    def plot_waterfall(self):
        # Calculate the earliest start time to align the x-axis to 0
        base_start_time = self.total_step_runtime[0]["start_time"]

        plt.figure(figsize=(20, 8))
        ax = plt.gca()

        color_cycle = cycle(self.event_color_scheme)
        event_colors = {}

        # Plot total step runtime (from run_step)
        for i, step in enumerate(self.total_step_runtime):
            duration = step["duration"]
            start_time = step["start_time"] - base_start_time  # Normalize to 0

            ax.barh(i, duration, left=start_time, color=self.step_color)
            ax.text(
                start_time + duration / 2,
                i - 0.45,
                f"{duration:.2f}s",
                ha="center",
                va="center",
            )

        # Plot each individual event on top of the step runtime
        for step_index, step in enumerate(self.agent_events):
            for event in step:
                duration = event["duration"]
                event_name = event["event_name"]
                start_time = event["start_time"] - base_start_time  # Normalize to 0

                if event_name not in event_colors:
                    event_colors[event_name] = next(color_cycle)

                color = event_colors[event_name]
                ax.barh(step_index, duration, left=start_time, color=color, alpha=1)
                ax.text(
                    start_time + duration / 2,
                    step_index,
                    f"{duration:.2f}s",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="black",
                    rotation=90,
                )

        ax.invert_yaxis()
        ax.set_yticks(range(len(self.total_step_runtime)))
        ax.set_yticklabels([f"Step {i+1}" for i in range(len(self.total_step_runtime))])
        ax.set_xlabel("Time (seconds)")
        ax.set_title("Agent Event Waterfall")

        # Add legend for event colors
        # Existing legend labels
        legend_labels = [
            plt.Line2D([0], [0], color=color, lw=4) for color in event_colors.values()
        ]

        # Adding the "Step" label in grey
        step_label = plt.Line2D([0], [0], color="grey", lw=4)
        legend_labels.append(step_label)

        # Update the legend to include "Step"
        ax.legend(
            legend_labels, list(event_colors.keys()) + ["Step"], title="Event Name"
        )

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)

        plt.close()

        return Image(buf.read())

    def get_summary_df(self):
        summary_data = {}

        # Iterate over each step and each event in the step
        for step_index, step_events in enumerate(self.agent_events):
            # Step row key
            step_key = f"Step {step_index + 1}"
            summary_data[step_key] = {}

            # Count the number of each event type in the step
            event_counts = {}

            # Iterate over each event in the step
            for event in step_events:
                event_name = event["event_name"]

                # Increment the count for the event
                if event_name not in event_counts:
                    event_counts[event_name] = 1
                else:
                    event_counts[event_name] += 1

                # for each key in the event, excluding 'event_name', 'start_time', and 'end_time', add the value to the summary
                for key, value in event.items():
                    if key not in ["event_name", "start_time", "end_time"]:
                        metric_key = f"{event_name} {key}"

                        if metric_key not in summary_data[step_key]:
                            summary_data[step_key][metric_key] = value
                        else:
                            summary_data[step_key][metric_key] += value

            # add the event counts
            for event_name, count in event_counts.items():
                count_key = f"{event_name} count"
                summary_data[step_key][count_key] = count

        # Convert the dictionary to a DataFrame
        df = pd.DataFrame(summary_data).T

        return df
