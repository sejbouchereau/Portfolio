-- Use the Students Depression database
USE [Students Depression]

-- Preview raw dataset before cleaning
SELECT * FROM [Dataset]

/* -----------------------------------------------------
   Standardize Gender Values
   Convert full text labels to short format (M / F)
   for consistency and easier visualization in Tableau
----------------------------------------------------- */

UPDATE [Dataset]
SET Gender = 'F' WHERE Gender = 'Female'

UPDATE [Dataset]
SET Gender = 'M' WHERE Gender = 'Male'


/* -----------------------------------------------------
   Create Age Groups for Dashboard Segmentation
   A1 = 18–24
   A2 = 25–30
   A3 = 31+
   Used in donut chart and age-based stress analysis
----------------------------------------------------- */

ALTER TABLE [Dataset]
ADD Age_Group VARCHAR(MAX)

UPDATE [Dataset]
SET Age_Group =
	CASE 
		WHEN Age BETWEEN 18 AND 24 THEN 'A1'
		WHEN Age BETWEEN 25 AND 30 THEN 'A2'
		ELSE 'A3'
	END

-- Validate Age grouping
SELECT Age, Age_Group 
FROM [Dataset] 
GROUP BY Age, Age_Group 
ORDER BY Age_Group;


/* -----------------------------------------------------
   Add Unique Index Column
   Useful for Tableau relationships and record counting
----------------------------------------------------- */

ALTER TABLE [Dataset]
ADD Index_Column INT IDENTITY(1,1)

-- Check column structure
SELECT * 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME LIKE 'Dataset'


/* -----------------------------------------------------
   Convert Binary Mental Health Fields
   Transform 0/1 values into readable Yes/No labels
   Improves dashboard clarity and user interpretation
----------------------------------------------------- */

-- Depression column
ALTER TABLE [Dataset]
ALTER COLUMN Depression VARCHAR(MAX)

UPDATE [Dataset]
SET Depression = 'No' WHERE Depression = '0'

UPDATE [Dataset]
SET Depression = 'Yes' WHERE Depression = '1'


-- Family Mental Health History column
ALTER TABLE [Dataset]
ALTER COLUMN Family_History_of_Mental_Illness VARCHAR(MAX)

UPDATE [Dataset]
SET Family_History_of_Mental_Illness = 'No' WHERE Family_History_of_Mental_Illness = '0'

UPDATE [Dataset]
SET Family_History_of_Mental_Illness = 'Yes' WHERE Family_History_of_Mental_Illness = '1'


-- Suicidal Thoughts column
ALTER TABLE [Dataset]
ALTER COLUMN Have_you_ever_had_suicidal_thoughts VARCHAR(MAX)

UPDATE [Dataset]
SET Have_you_ever_had_suicidal_thoughts = 'No' WHERE Have_you_ever_had_suicidal_thoughts = '0'

UPDATE [Dataset]
SET Have_you_ever_had_suicidal_thoughts = 'Yes' WHERE Have_you_ever_had_suicidal_thoughts = '1'

-- Preview cleaned binary columns
SELECT * FROM [Dataset]


/* -----------------------------------------------------
   Ensure Numerical Data Types for Aggregation
   Required for KPI cards and average calculations
----------------------------------------------------- */

-- Convert Study Hours to numeric for proper aggregation
ALTER TABLE [Dataset]
ALTER COLUMN Study_Hours FLOAT


/* -----------------------------------------------------
   Convert Sleep Duration (Categorical) to Numeric
   Required to calculate average sleep hours in KPI card
   and support numerical analysis in Tableau
----------------------------------------------------- */

-- Remove existing numeric column if previously created
ALTER TABLE [Dataset]
DROP COLUMN Sleep_Duration_Numeric;

-- Create new numeric sleep column
ALTER TABLE [Dataset]
ADD Sleep_Duration_Numeric FLOAT

-- Map categorical sleep ranges to representative numeric values
UPDATE [Dataset]
SET Sleep_Duration_Numeric = 
    CASE
        WHEN Sleep_Duration = 'Less than 5 hours' THEN 4
        WHEN Sleep_Duration = '5-6 hours' THEN 5.5
        WHEN Sleep_Duration = '7-8 hours' THEN 7.5
        ELSE 9
    END;

/* 
Sleep_Duration_Numeric is used to:
- Calculate Average Sleep Hours (KPI card)
- Enable numerical comparisons
- Maintain analytical consistency across stress metrics
*/