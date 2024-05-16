import os
import ast
import matplotlib.pyplot as plt

path_of_the_directory= './files/processedfiles'
biden_features = {"positive": 0, "neutral": 0, "negative": 0}
trump_features = {"positive": 0, "neutral": 0, "negative": 0}
for filename in os.listdir(path_of_the_directory):
    f = os.path.join(path_of_the_directory,filename)
    if os.path.isfile(f):
        # print(f)
        # Open the text file and read its contents
        with open(f, "r") as file:
            lines = file.readlines()
            current_sentiment = None
            current_key = None
            for i, line in enumerate(lines):
                line = line.strip()  # Remove leading/trailing whitespace
                # Check if the line starts with "biden_sentiment" or "trump_sentiment"
                if "biden_sentiment" in line:
                    current_sentiment = biden_features
                    current_key = "biden_sentiment"
                    # Read the next three lines and get the float values
                    values = []
                    for next_line in lines[i+1:i+4]:
                        if "," in next_line:
                            value = float(next_line.split(": ")[1].strip().rstrip(','))
                        else:
                            value = float(next_line.split(": ")[1].strip().rstrip('\n'))
                        values.append(value)

                    # Increment the feature set with the largest value
                    max_value = max(values)
                    if max_value == values[0]:
                        biden_features["positive"] += 1
                    elif max_value == values[1]:
                        biden_features["neutral"] += 1
                    else:
                        biden_features["negative"] += 1
                elif "trump_sentiment" in line:
                    current_sentiment = trump_features
                    current_key = "trump_sentiment"
                    values = []
                    for next_line in lines[i+1:i+4]:
                        if "," in next_line:
                            value = float(next_line.split(": ")[1].strip().rstrip(','))
                        else:
                            value = float(next_line.split(": ")[1].strip().rstrip('\n'))
                        values.append(value)

                    # Increment the feature set with the largest value
                    max_value = max(values)
                    if max_value == values[0]:
                        trump_features["positive"] += 1
                    elif max_value == values[1]:
                        trump_features["neutral"] += 1
                    else:
                        trump_features["negative"] += 1

# Print the maximum values for each feature
print("Biden Features:")
for feature, value in biden_features.items():
    print(f"{feature.capitalize()}: {value}")

print("\nTrump Features:")
for feature, value in trump_features.items():
    print(f"{feature.capitalize()}: {value}")

# Extracting the keys (categories) and values for both Biden and Trump
categories = list(biden_features.keys())
biden_values = list(biden_features.values())
trump_values = list(trump_features.values())

# Setting the positions and width for the bars
bar_width = 0.35
index = range(len(categories))

# Creating the bar graph
fig, ax = plt.subplots()
bar1 = ax.bar(index, biden_values, bar_width, label='Biden')
bar2 = ax.bar([i + bar_width for i in index], trump_values, bar_width, label='Trump')

# Adding labels, title, and legend
ax.set_xlabel('Sentiment')
ax.set_ylabel('Values')
ax.set_title('Sentiment Analysis Comparison between Biden and Trump')
ax.set_xticks([i + bar_width / 2 for i in index])
ax.set_xticklabels(categories)
ax.legend()

# Displaying the bar graph
plt.show()
