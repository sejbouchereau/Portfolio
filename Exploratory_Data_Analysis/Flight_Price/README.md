# ✈️ Flight Price Feature Engineering



Feature engineering project on airline ticket data to prepare variables for machine learning models predicting flight prices.



## Key Highlights



* Parsed and split date and time features into day, month, year, hour, and minute.
* Converted text-based stops and duration information into numeric values.
* Handled missing values and removed non-informative columns (Route, Additional\_Info).
* Applied One-Hot Encoding to categorical columns (Airline, Source, Destination).
* Combined cleaned and encoded features into a final structured dataset ready for modeling.



## Insights



* Time-based features such as departure and arrival hours significantly improve model interpretability.
* Numeric encoding of stops and duration allows for better correlation analysis with ticket prices.
* Feature engineering reduced noise and created a consistent dataset for regression modeling.



## 🧠 Technologies



Python, Pandas, NumPy, Scikit-learn (One-hot encoding)

