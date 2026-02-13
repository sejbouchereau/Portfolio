USE [Students Depression]

SELECT * FROM [Depression+Student+Dataset]

UPDATE [Depression+Student+Dataset]
SET Gender = 'F' WHERE Gender = 'Female'

UPDATE [Depression+Student+Dataset]
SET Gender = 'M' WHERE Gender = 'Male'

ALTER TABLE [Depression+Student+Dataset]
ADD Age_Group VARCHAR(MAX)

UPDATE [Depression+Student+Dataset]
SET Age_Group =
	CASE WHEN Age BETWEEN 18 AND 24 THEN 'A1'
	ELSE CASE WHEN Age BETWEEN 25 AND 30 THEN 'A2'
	ELSE 'A3'
	END
END

SELECT Age, Age_Group FROM [Depression+Student+Dataset] GROUP BY Age, Age_Group ORDER BY Age_Group;

ALTER TABLE [Depression+Student+Dataset]
ADD Index_Column INT IDENTITY(1,1)

SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME LIKE 'Depression+Student+Dataset'

ALTER TABLE [Depression+Student+Dataset]
ALTER COLUMN Depression VARCHAR(MAX)

UPDATE [Depression+Student+Dataset]
SET Depression = 'No' WHERE Depression = '0'

UPDATE [Depression+Student+Dataset]
SET Depression = 'Yes' WHERE Depression = '1'

ALTER TABLE [Depression+Student+Dataset]
ALTER COLUMN Family_History_of_Mental_Illness VARCHAR(MAX)

UPDATE [Depression+Student+Dataset]
SET Family_History_of_Mental_Illness = 'No' WHERE Family_History_of_Mental_Illness = '0'

UPDATE [Depression+Student+Dataset]
SET Family_History_of_Mental_Illness = 'Yes' WHERE Family_History_of_Mental_Illness = '1'

ALTER TABLE [Depression+Student+Dataset]
ALTER COLUMN Have_you_ever_had_suicidal_thoughts VARCHAR(MAX)

UPDATE [Depression+Student+Dataset]
SET Have_you_ever_had_suicidal_thoughts = 'No' WHERE Have_you_ever_had_suicidal_thoughts = '0'

UPDATE [Depression+Student+Dataset]
SET Have_you_ever_had_suicidal_thoughts = 'Yes' WHERE Have_you_ever_had_suicidal_thoughts = '1'

SELECT * FROM [Depression+Student+Dataset]

ALTER TABLE [Depression+Student+Dataset]
ALTER COLUMN Study_Hours FLOAT

ALTER TABLE [Depression+Student+Dataset]
DROP COLUMN Sleep_Duration_Numeric;

ALTER TABLE [Depression+Student+Dataset]
ADD Sleep_Duration_Numeric FLOAT

UPDATE [Depression+Student+Dataset]
SET Sleep_Duration_Numeric = 
    CASE
        WHEN Sleep_Duration = 'Less than 5 hours' THEN 4
        WHEN Sleep_Duration = '5-6 hours' THEN 5.5
        WHEN Sleep_Duration = '7-8 hours' THEN 7.5
        ELSE 9
    END;