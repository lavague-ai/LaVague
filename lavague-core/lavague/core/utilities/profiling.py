import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from functools import wraps
import io
from IPython.display import display, Image
from itertools import cycle

# stores llm and retriever calls
agent_events = []

# stores total runtime of each step
agent_steps = []

# call before each agent step to group events by steps
def start_new_step():
    global agent_events
    agent_events.append([])

# track the runtime of the run_step function
def track_total_runtime():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            agent_steps.append({
                'start_time': start_time,
                # 'end_time': end_time,
                'duration': duration
            })
            return result
        return wrapper
    return decorator

# track runtime, prompt size, and completion size of a llm call (used on world model + action engine)
def track_llm_call(event_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            
            agent_events[-1].append({
                'event_name': event_name,
                'start_time': start_time,
                # 'end_time': end_time,
                'duration': duration,
                'prompt_size': len(args[0]),
                'completion_size': len(result.text)
            })
            return result
        return wrapper
    return decorator

# track runtime and html size of a retriever call
def track_retriever(event_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            
            agent_events[-1].append({
                'event_name': event_name,
                'start_time': start_time,
                # 'end_time': end_time,
                'duration': duration,
                'html_size': len(args[0].driver.get_html()),
            })
            return result
        return wrapper
    return decorator


class ChartGenerator:
    def __init__(self, agent_events, agent_steps):
        self.agent_events = agent_events
        self.total_step_runtime = agent_steps
        self.step_color = "lightgrey"
        self.event_color_scheme = ["lightblue", "bisque", "thistle", "lightgreen", "pink"]

    def plot_waterfall(self):
        # Calculate the earliest start time to align the x-axis to 0
        base_start_time = self.total_step_runtime[0]['start_time']
        
        plt.figure(figsize=(20, 8))
        ax = plt.gca()
    
        color_cycle = cycle(self.event_color_scheme)
        event_colors = {}
        
        # Plot total step runtime (from run_step)
        for i, step in enumerate(self.total_step_runtime):
            duration = step['duration']
            start_time = step['start_time'] - base_start_time  # Normalize to 0
            
            ax.barh(i, duration, left=start_time, color=self.step_color)
            ax.text(start_time + duration / 2, i - 0.45, f"{duration:.2f}s",
                    ha='center', va='center')
        
        # Plot each individual event on top of the step runtime
        for step_index, step in enumerate(self.agent_events):
            for event in step:
                duration = event['duration']
                event_name = event['event_name']
                start_time = event['start_time'] - base_start_time  # Normalize to 0
                
                if event_name not in event_colors:
                    event_colors[event_name] = next(color_cycle)
                
                color = event_colors[event_name]
                ax.barh(step_index, duration, left=start_time, color=color)
                ax.text(start_time + duration / 2, step_index, f"{duration:.2f}s",
                        ha='center', va='center', fontsize=9, color='black', rotation=90)
        
        ax.invert_yaxis()
        ax.set_yticks(range(len(self.total_step_runtime)))
        ax.set_yticklabels([f'Step {i+1}' for i in range(len(self.total_step_runtime))])
        ax.set_xlabel('Time (seconds)')
        ax.set_title('Waterfall Chart with Events Overlay')

        
        # Add legend for event colors
        legend_labels = [plt.Line2D([0], [0], color=color, lw=4) for color in event_colors.values()]
        ax.legend(legend_labels, event_colors.keys(), title="Event Name")
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
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
                event_name = event['event_name']
                
                # Increment the count for the event
                if event_name not in event_counts:
                    event_counts[event_name] = 1
                else:
                    event_counts[event_name] += 1
                
                # for each key in the event, excluding 'event_name', 'start_time', and 'end_time', add the value to the summary
                for key, value in event.items():
                    if key not in ['event_name', 'start_time', 'end_time']:
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