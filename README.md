# JPMCB_customer_clusterization
Customer complaint ML model trained on CFPB Complaint Database against JPMorgan Chase & Co. and year 2025. Interactive dashboard summarizing results in Power BI was added.

# Features:
1. **Redaction cleaning:** In order to omit sensitive information hidden by XXXX redaction cleaning was performed via regular expressions
2. **Models and tools considering the context**: For this specific task of unsupervised clustering of text documents specific models and tools were used.
   a. _Lemmatization_ during data preparation.
   b. _TF-IDF Vectorization_ and _K-Means clustering_ for complaint clustering.
   c. _Elbow method_ for finding optimal number of clusters.
   d. Manual labelling of the groups based on their lemmas and sample complaints.
3. **Interactive dashboard:** Results were imported to Power BI and interactive dashboards was created. Dashboard contains several elements
   a. _Bar chart_ that shows number of complaints by groups.
   b. _Line chart _that shows how these numbers change throughout the year for each of the groups.
   c. _Donut chart_ that shows how complaints are distributed by every US state.
   d. _Filters_ for selecting time period and complaint platform.
