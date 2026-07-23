--------------------------------------------------------------------------------
-- linz_schema_views.sql
-- Creates basic views of LINZ tables for GIS queries
-- Author:  Grant Pearson
-- Created: Jun 4, 2025
--------------------------------------------------------------------------------

--DEPENDENCIES--{nz_primary_land_parcels nz_title_parcel_association_list nz_property_titles}
CREATE OR REPLACE VIEW {schema}.nz_parcel_titles_vw as
select p.id parcel_id, p.appellation, p.affected_surveys, p.parcel_intent, p.topology_type, p.statutory_actions,
  ifnull(p.land_district, t.land_district) land_district,
  p.titles, p.survey_area, p.calc_area,
 tp.source,
 t.id title_id, t.title_no, t.status title_status, t.type title_type, t.issue_date, t.guarantee_status,
  t.estate_description, t.number_owners, t.spatial_extents_shared
from {schema}.nz_primary_land_parcels p
 INNER JOIN {schema}.nz_title_parcel_association_list tp ON p.id = tp.par_id 
 INNER JOIN {schema}.nz_property_titles t ON tp.title_no = t.title_no 
 ;

--DEPENDENCIES--{nz_primary_land_parcels nz_title_parcel_association_list nz_property_titles_list}
CREATE OR REPLACE VIEW {schema}.nz_parcel_titles_vw as
select p.id parcel_id, p.appellation, p.affected_surveys, p.parcel_intent, p.topology_type, p.statutory_actions,
  ifnull(p.land_district, t.land_district) land_district,
  p.titles, p.survey_area, p.calc_area,
 tp.source,
 t.id title_id, t.title_no, t.status title_status, t.register_type, t.type title_type,
  t.issue_date, t.guarantee_status, t.provisional,
  t.title_no_srs, t.title_no_head_srs, t.survey_reference, t.maori_land, t.number_owners
from {schema}.nz_primary_land_parcels p
 INNER JOIN {schema}.nz_title_parcel_association_list tp ON p.id = tp.par_id 
 INNER JOIN {schema}.nz_property_titles_list t ON tp.title_no = t.title_no 
 ;

--DEPENDENCIES--{nz_primary_land_parcels nz_title_parcel_association_list nz_property_titles nz_property_title_estates_list nz_property_titles_owners_list}
CREATE OR REPLACE VIEW {schema}.nz_parcel_owners_vw as
select p.id parcel_id,
  ifnull(ifnull(ifnull(p.land_district, t.land_district), e.land_district), o.land_district) land_district,
 tp.source,
 t.id title_id, t.title_no, t.status title_status, t.type title_type, t.issue_date, t.guarantee_status,
  t.estate_description, t.number_owners, t.spatial_extents_shared,
 e.id title_estate_id, e.status estate_status, e.type estate_type, e.share, e.purpose, e.timeshare_week_no, e.term,
  e.legal_description, e.area,
 o.id owner_id, o.status owner_status, o.estate_share, o.owner_type, o.prime_surname, o.prime_other_names, o.corporate_name, o.name_suffix
from {schema}.nz_primary_land_parcels p
 INNER JOIN {schema}.nz_title_parcel_association_list tp ON p.id = tp.par_id 
 INNER JOIN {schema}.nz_property_titles t ON tp.title_no = t.title_no 
 INNER JOIN {schema}.nz_property_title_estates_list e ON t.title_no = e.title_no 
 INNER JOIN {schema}.nz_property_titles_owners_list o ON e.id = o.tte_id 
;

--DEPENDENCIES--{nz_primary_land_parcels nz_title_parcel_association_list nz_property_titles_list nz_property_title_estates_list nz_property_titles_owners_list}
CREATE OR REPLACE VIEW {schema}.nz_parcel_owners_vw as
select p.id parcel_id,
  ifnull(ifnull(ifnull(p.land_district, t.land_district), e.land_district), o.land_district) land_district,
 tp.source,
 t.id title_id, t.title_no, t.status title_status, t.type title_type, t.issue_date, t.guarantee_status,
  t.maori_land, t.number_owners,
 e.id title_estate_id, e.status estate_status, e.type estate_type, e.share, e.purpose, e.timeshare_week_no, e.term,
  e.legal_description, e.area,
 o.id owner_id, o.status owner_status, o.estate_share, o.owner_type, o.prime_surname, o.prime_other_names, o.corporate_name, o.name_suffix
from {schema}.nz_primary_land_parcels p
 INNER JOIN {schema}.nz_title_parcel_association_list tp ON p.id = tp.par_id 
 INNER JOIN {schema}.nz_property_titles_list t ON tp.title_no = t.title_no 
 INNER JOIN {schema}.nz_property_title_estates_list e ON t.title_no = e.title_no 
 INNER JOIN {schema}.nz_property_titles_owners_list o ON e.id = o.tte_id 
;

--DEPENDENCIES--{nz_primary_land_parcels nz_title_parcel_association_list nz_property_titles nz_property_title_estates_list nz_property_titles_owners_list}
CREATE OR REPLACE VIEW {schema}.nz_parcel_owners_list_vw as
select p.id parcel_id,
 count(t.id) num_titles,
 o.status owner_status, o.estate_share, o.owner_type, ifnull(o.corporate_name, concat(o.prime_other_names, ' ', o.prime_surname)) owner_name
from {schema}.nz_primary_land_parcels p
 INNER JOIN {schema}.nz_title_parcel_association_list tp ON p.id = tp.par_id 
 INNER JOIN {schema}.nz_property_titles t ON tp.title_no = t.title_no 
 INNER JOIN {schema}.nz_property_title_estates_list e ON t.title_no = e.title_no 
 INNER JOIN {schema}.nz_property_titles_owners_list o ON e.id = o.tte_id 
group by p.id,
 o.status, o.estate_share, o.owner_type, o.corporate_name, o.prime_surname, o.prime_other_names
;

--DEPENDENCIES--{nz_primary_land_parcels nz_title_parcel_association_list nz_property_titles_list nz_property_title_estates_list nz_property_titles_owners_list}
CREATE OR REPLACE VIEW {schema}.nz_parcel_owners_list_vw as
select p.id parcel_id,
 count(t.id) num_titles,
 o.status owner_status, o.estate_share, o.owner_type, ifnull(o.corporate_name, concat(o.prime_other_names, ' ', o.prime_surname)) owner_name
from {schema}.nz_primary_land_parcels p
 INNER JOIN {schema}.nz_title_parcel_association_list tp ON p.id = tp.par_id 
 INNER JOIN {schema}.nz_property_titles_list t ON tp.title_no = t.title_no 
 INNER JOIN {schema}.nz_property_title_estates_list e ON t.title_no = e.title_no 
 INNER JOIN {schema}.nz_property_titles_owners_list o ON e.id = o.tte_id 
group by p.id,
 o.status, o.estate_share, o.owner_type, o.corporate_name, o.prime_surname, o.prime_other_names
;

--DEPENDENCIES--{nz_property_titles nz_property_title_estates_list nz_property_titles_owners_list}
CREATE OR REPLACE VIEW {schema}.nz_title_owners_vw as
select distinct  t.id title_id, t.title_no, t.status title_status, t.type title_type, t.issue_date, t.guarantee_status,
  t.estate_description, t.number_owners, t.spatial_extents_shared,
  ifnull(ifnull(t.land_district, e.land_district), o.land_district) land_district,
 e.id title_estate_id, e.status estate_status, e.type estate_type, e.share, e.purpose, e.timeshare_week_no, e.term,
  e.legal_description, e.area,
 o.id owner_id, o.status owner_status, o.estate_share, o.owner_type, o.prime_surname, o.prime_other_names, o.corporate_name, o.name_suffix
from {schema}.nz_property_titles t 
 INNER JOIN {schema}.nz_property_title_estates_list e ON t.title_no = e.title_no 
 INNER JOIN {schema}.nz_property_titles_owners_list o ON e.id = o.tte_id 
;

--DEPENDENCIES--{nz_property_titles_list nz_property_title_estates_list nz_property_titles_owners_list}
CREATE OR REPLACE VIEW {schema}.nz_title_owners_vw as
select distinct  t.id title_id, t.title_no, t.status title_status, t.type title_type, t.issue_date, t.guarantee_status,
  t.maori_land, t.number_owners,
  ifnull(ifnull(t.land_district, e.land_district), o.land_district) land_district,
 e.id title_estate_id, e.status estate_status, e.type estate_type, e.share, e.purpose, e.timeshare_week_no, e.term,
  e.legal_description, e.area,
 o.id owner_id, o.status owner_status, o.estate_share, o.owner_type, o.prime_surname, o.prime_other_names, o.corporate_name, o.name_suffix
from {schema}.nz_property_titles_list t 
 INNER JOIN {schema}.nz_property_title_estates_list e ON t.title_no = e.title_no 
 INNER JOIN {schema}.nz_property_titles_owners_list o ON e.id = o.tte_id 
;

--DEPENDENCIES--{nz_property_titles landonline_title_encumbrance landonline_encumbrance}
CREATE OR REPLACE VIEW {schema}.nz_title_encumbrances_vw as
select distinct  t.id title_id, t.title_no, t.status title_status, t.type title_type, t.issue_date, t.guarantee_status,
  t.estate_description, t.number_owners, t.spatial_extents_shared, t.land_district,
 te.id title_encumbrance_id, te.enc_id encumbrance_id, te.status title_encumbrance_status,
  te.act_tin_id_crt te_act_tin_id_crt, te.act_id_crt te_act_id_crt,
 e.status encumbrance_status,
  e.act_tin_id_orig e_act_tin_id_orig, e.act_tin_id_crt e_act_tin_id_crt, e.act_id_crt e_act_id_crt, e.act_id_orig e_act_id_orig,
  e.term
from {schema}.nz_property_titles t
 INNER JOIN {schema}.landonline_title_encumbrance te ON t.title_no = te.ttl_title_no
 LEFT OUTER JOIN {schema}.landonline_encumbrance e ON te.enc_id = e.id
;

--DEPENDENCIES--{nz_property_titles_list landonline_title_encumbrance landonline_encumbrance}
CREATE OR REPLACE VIEW {schema}.nz_title_encumbrances_vw as
select distinct  t.id title_id, t.title_no, t.status title_status, t.type title_type, t.issue_date, t.guarantee_status,
  t.maori_land, t.number_owners, t.land_district,
 te.id title_encumbrance_id, te.enc_id encumbrance_id, te.status title_encumbrance_status,
  te.act_tin_id_crt te_act_tin_id_crt, te.act_id_crt te_act_id_crt,
 e.status encumbrance_status,
  e.act_tin_id_orig e_act_tin_id_orig, e.act_tin_id_crt e_act_tin_id_crt, e.act_id_crt e_act_id_crt, e.act_id_orig e_act_id_orig,
  e.term
from {schema}.nz_property_titles_list t
 INNER JOIN {schema}.landonline_title_encumbrance te ON t.title_no = te.ttl_title_no
 LEFT OUTER JOIN {schema}.landonline_encumbrance e ON e.id = te.enc_id
;

--DEPENDENCIES--{landonline_encumbrance landonline_encumbrance_share landonline_encumbrancee}
CREATE OR REPLACE VIEW {schema}.nz_title_encumbrance_shares_vw as
select distinct  e.id encumbrance_id, e.status encumbrance_status, e.act_tin_id_orig, e.act_tin_id_crt, e.act_id_crt, e.act_id_orig, e.term,
 es.id encumbrance_share_id, es.status encumbrance_share_status,
  es.act_tin_id_crt es_act_tin_id_crt, es.act_id_crt es_act_id_crt, es.act_id_ext es_act_id_ext, es.act_tin_id_ext es_act_tin_id_ext,
  es.system_crt es_system_crt, es.system_ext es_system_ext,
 ee.id encumbrancee_id, ee.status encumbrancee_status, ee.name encumbrancee_name
from {schema}.landonline_encumbrance e
 INNER JOIN {schema}.landonline_encumbrance_share es ON e.id = es.enc_id
 INNER JOIN {schema}.landonline_encumbrancee ee ON es.id = ee.ens_id
;

--DEPENDENCIES--{nz_properties_unit_of_property nz_properties_property_title_reference nz_properties_property_address_reference nz_properties_parent_property nz_properties_perspective nz_property_titles nz_property_boundaries}
CREATE OR REPLACE VIEW {schema}.properties_details_vw as
SELECT u.unit_of_property_id, u.property_name,
 tr.title_no,
 t.estate_description, t.land_district,
 pb.valuation_reference, pb.legal_description, pb.title_type, pb.territorial_authority, pb.area, pb.parcel_id,
 par.address_id,
 ppp.parent_unit_of_property_id,
 cppp.unit_of_property_id child_unit_of_property_id,
 pp.perspective_type, pp.source_id, pp.organisation_id
FROM {schema}.nz_properties_unit_of_property u
LEFT OUTER JOIN {schema}.nz_properties_property_title_reference tr ON tr.unit_of_property_id = u.unit_of_property_id 
LEFT OUTER JOIN {schema}.nz_property_titles t ON t.title_no = tr.title_no 
LEFT OUTER JOIN {schema}.nz_property_boundaries pb ON pb.unit_of_property_id = u.unit_of_property_id
LEFT OUTER JOIN {schema}.nz_properties_property_address_reference par ON par.unit_of_property_id = u.unit_of_property_id
LEFT OUTER JOIN {schema}.nz_properties_parent_property ppp ON ppp.unit_of_property_id = u.unit_of_property_id
LEFT OUTER JOIN {schema}.nz_properties_parent_property cppp ON cppp.parent_unit_of_property_id = u.unit_of_property_id
LEFT OUTER JOIN {schema}.nz_properties_perspective pp ON pp.unit_of_property_id = u.unit_of_property_id
;

--DEPENDENCIES--{nz_properties_unit_of_property nz_properties_property_title_reference nz_properties_property_address_reference nz_properties_parent_property nz_properties_perspective nz_property_titles nz_addresses nz_property_boundaries}
CREATE OR REPLACE VIEW {schema}.properties_details_vw as
SELECT u.unit_of_property_id, u.property_name,
 tr.title_no,
 t.estate_description, t.land_district,
 pb.valuation_reference, pb.legal_description, pb.title_type, pb.territorial_authority, pb.area, pb.parcel_id,
 par.address_id,
 a.road_id, a.address_number, a.address_number_suffix, a.unit, a.full_address_number,
  a.full_road_name, a.suburb_locality, a.town_city, a.full_address, 
 ppp.parent_unit_of_property_id,
 cppp.unit_of_property_id child_unit_of_property_id,
 pp.perspective_type, pp.source_id, pp.organisation_id
FROM {schema}.nz_properties_unit_of_property u
LEFT OUTER JOIN {schema}.nz_properties_property_title_reference tr ON tr.unit_of_property_id = u.unit_of_property_id 
LEFT OUTER JOIN {schema}.nz_property_titles t ON t.title_no = tr.title_no 
LEFT OUTER JOIN {schema}.nz_property_boundaries pb ON pb.unit_of_property_id = u.unit_of_property_id
LEFT OUTER JOIN {schema}.nz_properties_property_address_reference par ON par.unit_of_property_id = u.unit_of_property_id
LEFT OUTER JOIN {schema}.nz_addresses a ON a.address_id = par.address_id
LEFT OUTER JOIN {schema}.nz_properties_parent_property ppp ON ppp.unit_of_property_id = u.unit_of_property_id
LEFT OUTER JOIN {schema}.nz_properties_parent_property cppp ON cppp.parent_unit_of_property_id = u.unit_of_property_id
LEFT OUTER JOIN {schema}.nz_properties_perspective pp ON pp.unit_of_property_id = u.unit_of_property_id
;

--DEPENDENCIES--{nz_properties_unit_of_property nz_properties_property_title_reference nz_properties_property_address_reference nz_properties_property_building_reference nz_building_outlines_all_sources}
CREATE OR REPLACE VIEW {schema}.properties_buildings_vw as
SELECT u.unit_of_property_id, u.property_name,
 tr.title_no,
 par.address_id,
 pbr.building_id,
 b.name, b.uses building_use, b.suburb_locality, b.town_city, b.territorial_authority,
  b.capture_method, b.capture_source_id, b.capture_source_name, b.capture_source_from, b.capture_source_to,
  b.building_outline_lifecycle, b.begin_lifespan,  b.end_lifespan, b.last_modified
FROM {schema}.nz_properties_unit_of_property u
INNER JOIN {schema}.nz_properties_property_building_reference pbr ON pbr.unit_of_property_id = u.unit_of_property_id
INNER JOIN {schema}.nz_building_outlines_all_sources b ON b.building_id = pbr.building_id
LEFT OUTER JOIN {schema}.nz_properties_property_title_reference tr ON tr.unit_of_property_id = u.unit_of_property_id 
LEFT OUTER JOIN {schema}.nz_properties_property_address_reference par ON par.unit_of_property_id = u.unit_of_property_id
WHERE b.building_outline_lifecycle = 'Current'
;

--DEPENDENCIES--{nz_properties_unit_of_property nz_properties_national_district_valuation_roll nz_properties_ownership nz_properties_zoning nz_properties_building_age nz_properties_mass_contour nz_properties_mass_view nz_properties_mass_scope_of_view nz_properties_mass_decks nz_properties_mass_workshop_or_laundry nz_properties_mass_other_improvements}
CREATE OR REPLACE VIEW {schema}.properties_valuation_details_vw as
SELECT u.unit_of_property_id, u.property_name,
 vr.valuation_no_roll, vr.valuation_no_assessment, vr.valuation_no_suffix, vr.district_ta_code, vr.situation_name,
 vr.legal_description, vr.land_area, vr.property_category,
 vr.ownership_code, npo.description ownership_description,
 vr.current_effective_valuation_date,
 vr.capital_value, vr.improvements_value, vr.land_value, vr.trees, vr.annual_value, vr.annual_value_indicator,
 vr.gross_rental, vr.no_of_bedrooms, vr.improvements_description,
 vr.zoning zoning_code, npz.description zoning_description,
 vr.actual_property_use, vr.units_of_use, vr.off_street_parking,
 vr.building_age_indicator, npba.description building_age_description,
  npba.summarised_description building_age_summarised_description, npba.full_description_location building_age_full_description_location,
 vr.building_condition_indicator,
 vr.building_construction_indicator,
 vr.building_site_coverage, vr.building_total_floor_area,
 vr.mass_contour, npmc.description mass_contour_description,
 vr.mass_view, npmv.description mass_view_description,
 vr.mass_scope_of_view, npmsov.description mass_scope_of_view_description,
 vr.mass_total_living_area,
 vr.mass_deck, npmd.description mass_deck_description,
 vr.mass_workshop_laundry, npmwol.description mass_workshop_laundry_description,
 vr.mass_other_improvements, npmoi.description mass_other_improvements_description,
 vr.mass_garage_freestanding, vr.mass_garaged_under_main_roof,
 vr.production, vr.sale_group
FROM {schema}.nz_properties_unit_of_property u
LEFT OUTER JOIN {schema}.nz_properties_national_district_valuation_roll vr ON vr.unit_of_property_id = u.unit_of_property_id 
LEFT OUTER JOIN {schema}.nz_properties_ownership npo ON npo.ownership_code = vr.ownership_code 
LEFT OUTER JOIN {schema}.nz_properties_zoning npz ON npz.zoning_code = vr.zoning
LEFT OUTER JOIN {schema}.nz_properties_building_age npba ON npba.age_code = vr.building_age_indicator 
LEFT OUTER JOIN {schema}.nz_properties_mass_contour npmc ON npmc.contour_code = vr.mass_contour 
LEFT OUTER JOIN {schema}.nz_properties_mass_view npmv ON npmv.view_code = vr.mass_view 
LEFT OUTER JOIN {schema}.nz_properties_mass_scope_of_view npmsov ON npmsov.scope_of_view_code = vr.mass_scope_of_view 
LEFT OUTER JOIN {schema}.nz_properties_mass_decks npmd ON npmd.decks_code = vr.mass_deck 
LEFT OUTER JOIN {schema}.nz_properties_mass_workshop_or_laundry npmwol ON npmwol.workshop_or_laundry_code = vr.mass_workshop_laundry 
LEFT OUTER JOIN {schema}.nz_properties_mass_other_improvements npmoi ON npmoi.other_improvements_code = vr.mass_other_improvements 
;
