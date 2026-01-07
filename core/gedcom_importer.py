"""GEDCOM-importer för att importera släktforskningsdata"""
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from persons.models import Person, PersonRelationship, RelationshipType
from django.contrib.auth.models import User
from django.db import transaction
from datetime import datetime
from pathlib import Path
import tempfile
import logging

logger = logging.getLogger(__name__)


class GedcomImporter:
    """Importera personer och relationer från GEDCOM-fil"""

    def __init__(self, user: User):
        self.user = user
        self.person_map = {}  # Mappar GEDCOM ID till Person objekt
        self.stats = {
            'persons_created': 0,
            'relationships_created': 0,
            'errors': []
        }

    def import_file(self, gedcom_file) -> dict:
        """
        Importera en GEDCOM-fil och returnera statistik

        Args:
            gedcom_file: UploadedFile objekt från Django

        Returns:
            dict med statistik om importen
        """
        try:
            with transaction.atomic():
                # Spara filen temporärt
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.ged', delete=False) as tmp_file:
                    for chunk in gedcom_file.chunks():
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name

                try:
                    # Parsa GEDCOM-filen
                    parser = Parser()
                    parser.parse_file(tmp_path, strict=False)

                    # Importera personer först
                    self._import_individuals(parser)
                    logger.info(f"Importerade {self.stats['persons_created']} personer")

                    # Importera relationer sedan
                    self._import_families(parser)
                    logger.info(f"Importerade {self.stats['relationships_created']} relationer")

                finally:
                    # Radera temporär fil
                    Path(tmp_path).unlink(missing_ok=True)

            return self.stats

        except Exception as e:
            logger.error(f"Fel vid GEDCOM-import: {str(e)}", exc_info=True)
            self.stats['errors'].append(f"Kritiskt fel: {str(e)}")
            raise

    def _import_individuals(self, parser: Parser):
        """Importera alla personer från GEDCOM-filen"""
        individuals = parser.get_element_list()

        for element in individuals:
            if isinstance(element, IndividualElement):
                try:
                    person = self._create_person_from_element(element)
                    if person:
                        # Mappar GEDCOM ID till Person objekt
                        gedcom_id = element.get_pointer()
                        self.person_map[gedcom_id] = person
                        self.stats['persons_created'] += 1
                except Exception as e:
                    logger.warning(f"Kunde inte importera person {element.get_pointer()}: {str(e)}")
                    self.stats['errors'].append(f"Person {element.get_pointer()}: {str(e)}")

    def _create_person_from_element(self, element: IndividualElement) -> Person:
        """Skapa Person från GEDCOM IndividualElement"""

        # Hämta namn
        name_tuple = element.get_name()
        firstname = ""
        surname = ""

        if name_tuple:
            # name_tuple är (förnamn, efternamn) eller bara en sträng
            if isinstance(name_tuple, tuple) and len(name_tuple) >= 2:
                firstname = name_tuple[0].strip() if name_tuple[0] else ""
                surname = name_tuple[1].strip() if name_tuple[1] else ""
            elif isinstance(name_tuple, str):
                # Parsa namn manuellt om det är en sträng
                parts = name_tuple.split('/')
                if len(parts) >= 2:
                    firstname = parts[0].strip()
                    surname = parts[1].strip()
                else:
                    firstname = name_tuple.strip()

        # Om inget namn finns, skippa denna person
        if not firstname and not surname:
            logger.warning(f"Person {element.get_pointer()} saknar namn, hoppar över")
            return None

        # Hämta födelsedatum
        birth_date = None
        birth_data = element.get_birth_data()
        if birth_data:
            birth_date = self._parse_gedcom_date(birth_data[0])

        # Hämta dödsdatum
        death_date = None
        death_data = element.get_death_data()
        if death_data:
            death_date = self._parse_gedcom_date(death_data[0])

        # Skapa directory_name från namn och födelsedatum
        directory_name = self._generate_directory_name(firstname, surname, birth_date)

        # Se till att directory_name är unikt för användaren
        directory_name = self._ensure_unique_directory_name(directory_name)

        # Skapa Person
        person = Person.objects.create(
            user=self.user,
            firstname=firstname,
            surname=surname,
            birth_date=birth_date,
            death_date=death_date,
            directory_name=directory_name,
            notes=f"Importerad från GEDCOM ({element.get_pointer()})"
        )

        return person

    def _import_families(self, parser: Parser):
        """Importera alla familjer (relationer) från GEDCOM-filen"""
        logger.info("Börjar importera familjer...")

        # Försök flera metoder för att hämta familjer
        family_elements = []

        # Metod 1: Försök get_family_elements() om den finns
        if hasattr(parser, 'get_family_elements'):
            try:
                family_elements = parser.get_family_elements()
                logger.info(f"Metod 1: get_family_elements() returnerade {len(family_elements)} familjer")
            except Exception as e:
                logger.debug(f"get_family_elements() misslyckades: {e}")

        # Metod 2: Om metod 1 inte fungerade, filtrera get_element_list()
        if not family_elements:
            all_elements = parser.get_element_list()
            logger.info(f"Metod 2: parser.get_element_list() returnerade {len(all_elements)} element totalt")

            # Logga några exempel på element-typer
            element_types = {}
            for elem in all_elements[:20]:  # Visa första 20
                elem_type = type(elem).__name__
                element_types[elem_type] = element_types.get(elem_type, 0) + 1
            logger.debug(f"Element-typer (första 20): {element_types}")

            # Filtrera ut FamilyElement
            for element in all_elements:
                if isinstance(element, FamilyElement):
                    family_elements.append(element)

            logger.info(f"Metod 2: Hittade {len(family_elements)} FamilyElement av totalt {len(all_elements)} element")

        # Metod 3: Om fortfarande inga familjer, försök söka efter FAM-tagg
        if not family_elements:
            logger.info("Metod 3: Försöker hitta element med FAM-tag...")
            all_elements = parser.get_element_list()
            for element in all_elements:
                if hasattr(element, 'get_tag') and element.get_tag() == 'FAM':
                    logger.debug(f"Hittade element med FAM-tag: {element}")
                    family_elements.append(element)

            logger.info(f"Metod 3: Hittade {len(family_elements)} element med FAM-tag")

        # Bearbeta familjer
        family_count = 0
        for family in family_elements:
            family_count += 1
            try:
                self._create_relationships_from_family(family, parser)
            except Exception as e:
                pointer = family.get_pointer() if hasattr(family, 'get_pointer') else 'okänd'
                logger.error(f"Kunde inte importera familj {pointer}: {str(e)}", exc_info=True)
                self.stats['errors'].append(f"Familj {pointer}: {str(e)}")

        logger.info(f"Bearbetade totalt {family_count} familjer")

        if family_count == 0:
            logger.warning("VARNING: Inga familjer (FAM-poster) hittades i GEDCOM-filen! Kontrollera att filen innehåller familjerelationer.")
            self.stats['errors'].append("Inga familjer hittades i GEDCOM-filen")

    def _create_relationships_from_family(self, family: FamilyElement, parser: Parser):
        """Skapa relationer från en FAM-post"""

        family_id = family.get_pointer()
        logger.debug(f"Bearbetar familj: {family_id}")

        # Hämta föräldrar - FamilyElement API använder andra metoder
        husband_id = None
        wife_id = None

        # Försök olika metoder för att hämta make/maka
        try:
            # Metod 1: get_husband_element()
            if hasattr(family, 'get_husband_element'):
                husband_elem = family.get_husband_element()
                if husband_elem and hasattr(husband_elem, 'get_pointer'):
                    husband_id = husband_elem.get_pointer()
        except:
            pass

        try:
            if hasattr(family, 'get_wife_element'):
                wife_elem = family.get_wife_element()
                if wife_elem and hasattr(wife_elem, 'get_pointer'):
                    wife_id = wife_elem.get_pointer()
        except:
            pass

        # Metod 2: Om metod 1 inte fungerade, försök med direkt sökning i element-barn
        if not husband_id or not wife_id:
            try:
                # Sök efter HUSB och WIFE taggar i elementets barn
                if hasattr(family, '_Element__children'):
                    for elem in family._Element__children:
                        if hasattr(elem, 'get_tag') and hasattr(elem, 'get_value'):
                            tag = elem.get_tag()
                            value = elem.get_value()
                            if tag == 'HUSB' and value:
                                husband_id = value
                                logger.debug(f"Hittade HUSB via direkt sökning: {husband_id}")
                            elif tag == 'WIFE' and value:
                                wife_id = value
                                logger.debug(f"Hittade WIFE via direkt sökning: {wife_id}")
            except Exception as e:
                logger.debug(f"Direkt sökning efter HUSB/WIFE misslyckades: {e}")

        husband = self.person_map.get(husband_id) if husband_id else None
        wife = self.person_map.get(wife_id) if wife_id else None

        logger.debug(f"Familj {family_id}: Husband={husband_id}, Wife={wife_id}")

        # Skapa make/maka-relation om båda finns
        if husband and wife:
            logger.debug(f"Skapar make/maka-relation mellan {husband} och {wife}")
            self._create_relationship(
                husband, wife,
                RelationshipType.SPOUSE,
                RelationshipType.SPOUSE
            )
        elif husband_id or wife_id:
            # Logga om vi har ID men inte hittar personen
            if husband_id and not husband:
                logger.warning(f"Hittade inte husband {husband_id} i person_map")
            if wife_id and not wife:
                logger.warning(f"Hittade inte wife {wife_id} i person_map")

        # Hämta barn - använd direkt sökning efter CHIL-taggar
        children_ids = []

        try:
            # Sök efter CHIL-taggar i elementets barn
            if hasattr(family, '_Element__children'):
                for elem in family._Element__children:
                    if hasattr(elem, 'get_tag') and hasattr(elem, 'get_value'):
                        tag = elem.get_tag()
                        if tag == 'CHIL':
                            child_pointer = elem.get_value()
                            if child_pointer:
                                children_ids.append(child_pointer)
                                logger.debug(f"Hittade CHIL: {child_pointer}")
        except Exception as e:
            logger.debug(f"Sökning efter CHIL-taggar misslyckades: {e}")

        logger.info(f"Familj {family_id}: Hittade {len(children_ids)} barn: {children_ids}")

        # Skapa förälder-barn-relationer
        for child_id in children_ids:
            child = self.person_map.get(child_id)

            if not child:
                logger.warning(f"Barn {child_id} finns inte i person_map (familj {family_id})")
                continue

            logger.debug(f"Skapar relationer för barn {child}")

            # Skapa förälder-barn-relationer
            if husband:
                logger.debug(f"Skapar relation: {husband} (förälder) -> {child} (barn)")
                self._create_relationship(
                    husband, child,
                    RelationshipType.PARENT,
                    RelationshipType.CHILD
                )

            if wife:
                logger.debug(f"Skapar relation: {wife} (förälder) -> {child} (barn)")
                self._create_relationship(
                    wife, child,
                    RelationshipType.PARENT,
                    RelationshipType.CHILD
                )

    def _create_relationship(
        self,
        person_a: Person,
        person_b: Person,
        rel_a_to_b: RelationshipType,
        rel_b_to_a: RelationshipType
    ):
        """Skapa en relation mellan två personer (undvik duplicering)"""

        logger.debug(f"Försöker skapa relation: {person_a} ({rel_a_to_b}) <-> {person_b} ({rel_b_to_a})")

        # Kontrollera om relationen redan finns (i båda riktningarna)
        existing = PersonRelationship.objects.filter(
            user=self.user,
            person_a=person_a,
            person_b=person_b
        ).first()

        if existing:
            logger.debug(f"Relation finns redan: {person_a} -> {person_b}")
            return  # Relation finns redan

        # Kontrollera omvänd riktning också
        existing_reverse = PersonRelationship.objects.filter(
            user=self.user,
            person_a=person_b,
            person_b=person_a
        ).first()

        if existing_reverse:
            logger.debug(f"Relation finns redan (omvänd): {person_b} -> {person_a}")
            return  # Relation finns redan

        try:
            # Skapa relationen (clean() kommer fixa kanonisk ordning)
            rel = PersonRelationship.objects.create(
                user=self.user,
                person_a=person_a,
                person_b=person_b,
                relationship_a_to_b=rel_a_to_b,
                relationship_b_to_a=rel_b_to_a,
                notes="Importerad från GEDCOM"
            )
            self.stats['relationships_created'] += 1
            logger.info(f"Relation skapad: {rel}")
        except Exception as e:
            logger.error(f"Kunde inte skapa relation mellan {person_a} och {person_b}: {str(e)}", exc_info=True)
            self.stats['errors'].append(f"Relation {person_a} <-> {person_b}: {str(e)}")

    def _parse_gedcom_date(self, date_str: str) -> datetime.date:
        """
        Parsa GEDCOM-datum till Python date

        GEDCOM-datum kan vara i olika format:
        - "31 DEC 1990"
        - "DEC 1990"
        - "1990"
        - "ABT 1990"
        - "BEF 1990"
        """
        if not date_str:
            return None

        # Ta bort kvalificerare (ABT, BEF, AFT, etc.)
        date_str = date_str.upper().strip()
        for prefix in ['ABT', 'BEF', 'AFT', 'EST', 'CAL', 'ABOUT', 'BEFORE', 'AFTER']:
            if date_str.startswith(prefix):
                date_str = date_str[len(prefix):].strip()

        # Månadsmappning
        months = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }

        parts = date_str.split()

        try:
            if len(parts) == 3:
                # Format: "31 DEC 1990"
                day = int(parts[0])
                month = months.get(parts[1], 1)
                year = int(parts[2])
                return datetime(year, month, day).date()

            elif len(parts) == 2:
                # Format: "DEC 1990" eller "31 1990"
                if parts[0] in months:
                    month = months[parts[0]]
                    year = int(parts[1])
                    return datetime(year, month, 1).date()
                else:
                    # Anta dag och år
                    day = int(parts[0])
                    year = int(parts[1])
                    return datetime(year, 1, day).date()

            elif len(parts) == 1:
                # Format: "1990"
                year = int(parts[0])
                return datetime(year, 1, 1).date()

        except (ValueError, KeyError):
            logger.warning(f"Kunde inte parsa datum: {date_str}")
            return None

        return None

    def _generate_directory_name(self, firstname: str, surname: str, birth_date: datetime.date) -> str:
        """Generera directory_name från namn och födelsedatum"""
        # Normalisera namn
        def normalize(s):
            if not s:
                return ""
            s = s.lower().strip()
            s = s.replace(' ', '_')
            s = s.replace('å', 'a').replace('ä', 'a').replace('ö', 'o')
            # Ta bort icke-alfanumeriska tecken förutom underscore och bindestreck
            s = ''.join(c for c in s if c.isalnum() or c in ['_', '-'])
            return s

        first_norm = normalize(firstname)
        sur_norm = normalize(surname)

        # Bygg directory_name
        parts = []
        if first_norm:
            parts.append(first_norm)
        if sur_norm:
            parts.append(sur_norm)

        directory_name = '_'.join(parts) if parts else 'unknown'

        # Lägg till födelsedatum om det finns
        if birth_date:
            directory_name = f"{directory_name}_{birth_date.strftime('%Y-%m-%d')}"

        return directory_name

    def _ensure_unique_directory_name(self, directory_name: str) -> str:
        """Säkerställ att directory_name är unikt för användaren"""
        original = directory_name
        counter = 1

        while Person.objects.filter(user=self.user, directory_name=directory_name).exists():
            directory_name = f"{original}_{counter}"
            counter += 1

        return directory_name
