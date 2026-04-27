import pandas as pd
import ast
import matplotlib.pyplot as plt

linestyle_map = {
    0: "solid",
    1: "dashed",
    2: "dotted",
    4: "dashdot"
}

def plot_metric_per_critique(df_grouped, metric, title):
    for critique in df_grouped["critique_attributes"].unique():
        subset = df_grouped[df_grouped["critique_attributes"] == critique]
        subset = subset.sort_values("softmax_alpha")

        n_attr = subset["n_attributes_selected"].iloc[0]
        linestyle = linestyle_map.get(n_attr, "solid")

        plt.plot(subset["softmax_alpha"], subset[metric], label=critique, linestyle=linestyle)
    
    plt.xlabel("alpha")
    plt.xticks([0.5, 1.0, 1.5])
    plt.ylabel(metric)
    plt.title(title)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Combinazione di attributi\nsu cui lavora la critique")
    plt.savefig("plot " + title + ".png", bbox_inches='tight')
    plt.close()

def plot_metric_grouped(df_grouped, metric, title):
    for n_critique in df_grouped["n_attributes_selected"].unique():
        subset = df_grouped[df_grouped["n_attributes_selected"] == n_critique]
        subset = subset.sort_values("softmax_alpha")

        n_attr = subset["n_attributes_selected"].iloc[0]
        linestyle = linestyle_map.get(n_attr, "solid")

        plt.plot(subset["softmax_alpha"], subset[metric], label=n_critique, linestyle=linestyle)
    
    plt.xlabel("alpha")
    plt.xticks([0.5, 1.0, 1.5])
    plt.ylabel(metric)
    plt.title(title)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Numero di attributi\nsu cui lavora la critique")
    plt.savefig("plot " + title + ".png", bbox_inches='tight')
    plt.close()

def build_dataframe(group_by_critique_combination):
    df = pd.read_csv("totresults.csv", sep=";")  # or your delimiter
    df_refined = df[df["n_results"] != 0]
    df_refined["n_attributes_selected"] = df_refined["critique_attributes"].apply(
        lambda x: len(ast.literal_eval(x))
    )
    df_refined["n_valid_tests"] = True
    group_by_attrs = ["softmax_alpha", "n_attributes_selected"]
    if group_by_critique_combination:
        group_by_attrs.append("critique_attributes")
    df_refined = df_refined.groupby(group_by_attrs).agg({"accuracy":"mean", "diversity":"mean", "serendipity":"mean", "n_valid_tests":"count"}).sort_values(["softmax_alpha","n_attributes_selected"])
    df_refined = df_refined.reset_index()
    df_refined.to_csv("StatisticheFinali"+ str(group_by_critique_combination) + ".csv", sep=";", index=False)
    return df_refined

def main():
    df1 = build_dataframe(True)
    df2 = build_dataframe(False)
    metrics = ["accuracy", "serendipity", "diversity"]   
    for metric in metrics:
        plot_metric_per_critique(df1, metric, f"{metric} su singole combinazioni di critique")  
        plot_metric_grouped(df2, metric, f"{metric} su gruppi di critique")  

# Main
if __name__ == '__main__':
    main()
