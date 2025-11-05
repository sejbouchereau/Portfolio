import pytest
import random
from Scraper import *


class TestNormalizeAddress:

    def test_normalize_address_chaine_vide(self):
        assert normalize_address('') == ''

    def test_normalize_address_seulement_espaces(self):
        assert normalize_address('   ') == ''

    def test_normalize_address_chaine_normale(self):
        assert normalize_address('  123 Rue Principale  ') == '123 rue principale'

    def test_normalize_address_chaine_en_majuscules(self):
        assert normalize_address('  123 RUE PRINCIPALE  ') == '123 rue principale'

    def test_normalize_address_chaine_mixte(self):
        assert normalize_address('  123 RuE PrInCiPaLe  ') == '123 rue principale'

    def test_normalize_address_espaces_a_l_interieur(self):
        assert normalize_address('  123    Rue   Principale  ') == '123    rue   principale'

    def test_normalize_address_avec_caracteres_speciaux(self):
        assert normalize_address('  123!@# Rue$$ Principale^&  ') == '123!@# rue$$ principale^&'


class TestDataframeToDictList:

    def test_dataframe_to_dict_list_valide(self):
        df = pd.DataFrame({
            'adresse': ['123 Rue Principale', '456 Avenue des Champs'],
            'ville': ['Montréal', 'Québec']
        })
        resultat_attendu = [
            {'adresse': '123 Rue Principale', 'ville': 'Montréal'},
            {'adresse': '456 Avenue des Champs', 'ville': 'Québec'}
        ]
        assert dataframe_to_dict_list(df) == resultat_attendu

    def test_dataframe_to_dict_list_vide(self):
        df = pd.DataFrame()
        resultat_attendu = []
        assert dataframe_to_dict_list(df) == resultat_attendu

    def test_dataframe_to_dict_list_colonnes_uniques(self):
        df = pd.DataFrame({
            'adresse': ['123 Rue Principale', '456 Avenue des Champs']
        })
        resultat_attendu = [
            {'adresse': '123 Rue Principale'},
            {'adresse': '456 Avenue des Champs'}
        ]
        assert dataframe_to_dict_list(df) == resultat_attendu

    def test_dataframe_to_dict_list_non_dataframe(self):
        with pytest.raises(ValueError, match="L'entrée doit être un DataFrame pandas."):
            dataframe_to_dict_list([1, 2, 3])


class TestFindDuplicates:

    def test_find_duplicates_avec_doublons(self):
        data = [
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"},
            {"Adresse": "456 Avenue des Champs", "Ville": "Québec"},
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"},
        ]
        resultat_attendu = [
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"}
        ]
        assert find_duplicates(data) == resultat_attendu

    def test_find_duplicates_sans_doublons(self):
        data = [
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"},
            {"Adresse": "456 Avenue des Champs", "Ville": "Québec"},
            {"Adresse": "789 Boulevard René-Lévesque", "Ville": "Trois-Rivières"},
        ]
        resultat_attendu = []
        assert find_duplicates(data) == resultat_attendu

    def test_find_duplicates_avec_donnees_vides(self):
        data = []
        resultat_attendu = []
        assert find_duplicates(data) == resultat_attendu

    def test_find_duplicates_avec_doublons_multiples(self):
        data = [
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"},
            {"Adresse": "456 Avenue des Champs", "Ville": "Québec"},
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"},
            {"Adresse": "456 Avenue des Champs", "Ville": "Québec"},
        ]
        resultat_attendu = [
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"},
            {"Adresse": "456 Avenue des Champs", "Ville": "Québec"},
        ]
        assert find_duplicates(data) == resultat_attendu

    def test_find_duplicates_avec_adresse_absente(self):
        data = [
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"},
            {"Ville": "Québec"},
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"},
        ]
        resultat_attendu = [
            {"Adresse": "123 Rue Principale", "Ville": "Montréal"}
        ]
        assert find_duplicates(data) == resultat_attendu


class TestAirtableOverflow:

    def test_overflow_aucun_listing(self):
        data = []
        resultat_attendu = False
        assert is_airtable_overflow(data) == resultat_attendu

    def test_overflow_un_listing(self):
        data = [{"Adresse": "123 Rue Principale", "Ville": "Laval"}]
        resultat_attendu = False
        assert is_airtable_overflow(data) == resultat_attendu

    def test_overflow_850_notice(self):
        adresses = ["123 Rue Principale", "456 Avenue des Champs", "789 Boulevard Saint-Laurent",
                    "101 Rue Sherbrooke Ouest", "222 Rue Saint-Joseph", "333 Rue du Faubourg", "444 Avenue des Pins",
                    "555 Rue de la Montagne", "666 Boulevard René-Lévesque", "777 Rue Notre-Dame Ouest",
                    "888 Avenue du Parc", "999 Boulevard Gouin Ouest"]
        villes = ["Montréal", "Québec", "Laval", "Boisbriand", "Terrebonne", "Mirabel"]

        data = [{"Adresse": random.choice(adresses), "Ville": random.choice(villes)} for _ in range(850)]
        resultat_attendu = False
        assert is_airtable_overflow(data) == resultat_attendu

    def test_overflow_950_saturation(self):
        adresses = ["123 Rue Principale", "456 Avenue des Champs", "789 Boulevard Saint-Laurent",
                    "101 Rue Sherbrooke Ouest", "222 Rue Saint-Joseph", "333 Rue du Faubourg", "444 Avenue des Pins",
                    "555 Rue de la Montagne", "666 Boulevard René-Lévesque", "777 Rue Notre-Dame Ouest",
                    "888 Avenue du Parc", "999 Boulevard Gouin Ouest"]
        villes = ["Montréal", "Québec", "Laval", "Boisbriand", "Terrebonne", "Mirabel"]

        data = [{"Adresse": random.choice(adresses), "Ville": random.choice(villes)} for _ in range(950)]
        resultat_attendu = True
        assert is_airtable_overflow(data) == resultat_attendu


if __name__ == "__main__":
    pytest.main()
