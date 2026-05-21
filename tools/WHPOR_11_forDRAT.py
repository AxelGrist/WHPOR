'''
WHPOR_11_forDRAT.py
Script: forDRAT Drought Risk Score
Purpose: Calculate per-watershed drought risk scores (2050 climate projection) by
         joining BC VRI2 vegetation data to the forDRAT lookup table (bcgov/forDRAT).
         Outputs Drought_Risk_Score_2050 and Drought_Risk_Class_2050 to the compiled
         watershed stats tables and feature classes for all three reporting scales
         (Named Watershed, Tributary Watersheds, Watershed Assessment Units).

         Run between WHPOR_09_CEA_watershed_analysis and WHPOR_10_Resultant_Outputs.

Date: 2026
Author: WHPOR Pipeline (C.Folkers et al.) — forDRAT extension

Dependencies:
    WHPOR_06_VRI2       — VRI2_resultant feature class in VRI2_AOI_{year}.gdb
    WHPOR_09_CEA        — Compiled_Watershed_Hazard_Summaries_rw.gdb
    forDrat.csv         — bcgov/forDRAT lookup table; place in:
                          \\spatialfiles.bcgov\...\WHPOR_Watershed_Analysis\working\source_data\

Score methodology:
    Per VRI2 polygon:
        1. Construct BGC variant key from BEC_ZONE_CODE + BEC_SUBZONE + BEC_VARIANT
        2. Map VRI MOISTURE_REGIME → forDRAT SMR integer (1=xeric … 5=subhygric)
        3. For each recognized species (SPECIES_CD_1..6):
               look up drought risk code (L/M/H/VH) in forDRAT 2050 table
               convert: L=1, M=2, H=3, VH=4
               weight by SPECIES_PCT
        4. Polygons with no recognized species/BGC match → excluded (unknown)
        5. polygon_score = ((weighted_avg − 1) / 3) × 100  [0–100 scale]

    Per watershed reporting unit:
        area-weighted mean of polygon_score over all scored (non-null) polygons

    Classification thresholds (0–100):
        L: < 25 | M: 25–49 | H: 50–74 | VH: ≥ 75

Map template note:
    To render Drought_Risk_Class_2050 on the PDF map, add layers named
    "Drought Risk Named Watershed", "Drought Risk Tributaries", "Drought Risk WAU"
    to the WHPOR_APRX_Template .aprx file, symbolized by Drought_Risk_Class_2050.
    The maps() function in WHPOR_10_Resultant_Outputs.py will automatically
    update their data sources when those layer names are present.

IMPORTANT — validate before operational use:
    VRI MOISTURE_REGIME → forDRAT SMR mapping (VRI_MR_TO_SMR below) should be
    confirmed against the official BC VRI data dictionary before first production run.
'''

import arcpy
import os
import datetime
import sys
import pandas as pd


class ForDRAT:
    def __init__(self, wtrshdname, Bfold):
        self.wtrshdname = wtrshdname
        self.Bfold = Bfold

        arcpy.env.overwriteOutput = True

        # ── user variables ──────────────────────────────────────────────────────
        WatershedName = wtrshdname
        BaseFolder    = Bfold

        # ── static paths ────────────────────────────────────────────────────────
        year = datetime.date.today().year

        fordrat_csv = (r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects'
                       r'\WHPOR_Watershed_Analysis\working\source_data\forDrat.csv')
        vri_str  = 'VRI2_AOI_' + str(year) + '.gdb'
        VRI2gdb  = os.path.join(BaseFolder, r'1_SpatialData\3_VRI_Update', 'data', vri_str)
        compiled_gdb = os.path.join(
            BaseFolder,
            r'1_SpatialData\4_CEA_Watershed_Analysis\Ouput'
            r'\Compiled_Watershed_Hazard_Summaries_rw.gdb'
        )

        # ── field name constants ─────────────────────────────────────────────────
        SCORE_FIELD = 'Drought_Risk_Score_2050'  # 0–100 numeric, joined to stats table + FC
        CLASS_FIELD = 'Drought_Risk_Class_2050'  # L / M / H / VH text, 10 chars
        VRI_SCR_FLD = 'FORDRAT_SCR_2050'         # intermediate per-polygon score on VRI2
        SCORE_X_AREA = 'fordrat_sxa'             # score × area temp field on intersect
        FORDRAT_PERIOD = '2050'
        wsLinkFld = 'RevRepUni'

        # ── forDRAT species column names (as they appear in forDrat.csv) ─────────
        FORDRAT_SPECIES_COLS = ['Pl', 'Sx', 'Fd', 'Bl', 'Cw', 'Hw', 'Lw', 'Py', 'Ac', 'At']

        # VRI SPECIES_CD_* code → forDRAT species column name
        # Species not in this dict → None → excluded (treated as unknown, no contribution to score)
        # Sx represents the hybrid spruce complex (Sx, Sw, Se)
        VRI_TO_FORDRAT = {
            # Spruce (Sx complex — all interior spruce and hybrids)
            'SX':  'Sx',  'SW':  'Sx',  'SE':  'Sx',
            'S':   'Sx',  'SXW': 'Sx',
            'SXE': 'Sx',  'SXL': 'Sx',  'SXS': 'Sx',
            # Douglas-fir (interior and coast)
            'FD':  'Fd',  'FDI': 'Fd',  'FDC': 'Fd',
            # True firs (Abies spp.)
            'BL':  'Bl',  'BA':  'Bl',  'BG':  'Bl',  'BP':  'Bl',
            'B':   'Bl',  # generic Abies (genus-level VRI code)
            'BB':  'Bl',  # balsam fir (A. balsamea — exotic, appears in Omineca VRI)
            'BM':  'Bl',  # Shasta red fir (A. magnifica — exotic, appears in Omineca VRI)
            # Cedar / Hemlock
            'CW':  'Cw',
            'HW':  'Hw',  'HM':  'Hw',
            'H':   'Hw',  # generic Hemlock (coarse VRI records)
            # Larch
            'LW':  'Lw',  'LA':  'Lw',  'LT':  'Lw',
            'L':   'Lw',  # generic Larch (coarse VRI records)
            # PY = Yellow Pine = Ponderosa Pine (official BC code)
            'PY':  'Py',
            # Pines (Pl complex)
            'PL':  'Pl',  'PLI': 'Pl',  'PLC': 'Pl',  'PJ':  'Pl',
            'PA':  'Pl',  # Whitebark Pine — closest forDRAT congener
            'PW':  'Pl',  # Western white pine (P. monticola) — no dedicated forDRAT col
            'P':   'Pl',  # generic Pine (coarse VRI records)
            # Cottonwood / Poplar / Aspen
            'AC':  'Ac',  'ACT': 'Ac',  'ACB': 'Ac',  'AX':  'Ac',
            'AT':  'At',
        }

        # VRI MOISTURE_REGIME integer → forDRAT SMR integer
        # VRI:     0=water, 1=wet(subhygric-hygric), 2=moist, 3=fresh(submesic),
        #          4=slightly dry(subxeric), 5=mod. dry(xeric), 6=very dry, 7=excess. dry
        # forDRAT: 1=xeric, 2=subxeric, 3=submesic, 4=mesic, 5=subhygric
        # NOTE: Validate this mapping against the BC VRI data dictionary before
        #       operational use. Sites wetter than subhygric (SMR>5) are outside
        #       forDRAT coverage and are excluded (None).
        VRI_MR_TO_SMR = {
            0: None,   # water / aquatic — exclude
            1:    5,   # wet / subhygric
            2:    4,   # moist / mesic
            3:    3,   # fresh / submesic
            4:    2,   # slightly dry / subxeric
            5:    1,   # moderately dry / xeric
            6:    1,   # very dry → clamp to xeric (closest forDRAT class)
            7: None,   # excessively dry — outside forDRAT range, exclude
        }

        RISK_TO_NUM = {'L': 1.0, 'M': 2.0, 'H': 3.0, 'VH': 4.0}

        def classify_score(score):
            """Convert 0–100 numeric score to L / M / H / VH drought risk class."""
            if score is None:
                return 'Unknown'
            if score >= 75.0:
                return 'VH'
            if score >= 50.0:
                return 'H'
            if score >= 25.0:
                return 'M'
            return 'L'

        # ══════════════════════════════════════════════════════════════════════════
        # 1. Load forDRAT CSV — filter to 2050, build lookup dict
        # ══════════════════════════════════════════════════════════════════════════
        print('\n' + '='*60)
        print('WHPOR_11_forDRAT: Loading forDRAT lookup table...')
        if not os.path.exists(fordrat_csv):
            print(f'ERROR: forDRAT CSV not found at:\n  {fordrat_csv}')
            sys.exit(1)

        df = pd.read_csv(fordrat_csv)
        df['Period'] = df['Period'].astype(str).str.strip()
        df_period = df[df['Period'] == FORDRAT_PERIOD]
        if len(df_period) == 0:
            print(f'ERROR: No rows found for period "{FORDRAT_PERIOD}" in forDRAT CSV.')
            print(f'  Available periods: {sorted(df["Period"].unique())}')
            sys.exit(1)
        print(f'  Period "{FORDRAT_PERIOD}": {len(df_period)} rows loaded')

        # Build lookup: (bgc_str, smr_int, fordrat_sp_col) → numeric_weight
        fordrat_lookup = {}
        for _, row in df_period.iterrows():
            bgc = str(row['BGC']).strip()
            smr = int(row['SMR'])
            for sp_col in FORDRAT_SPECIES_COLS:
                code = str(row[sp_col]).strip()
                if code in RISK_TO_NUM:
                    fordrat_lookup[(bgc, smr, sp_col)] = RISK_TO_NUM[code]
        print(f'  Lookup entries built: {len(fordrat_lookup)}')

        # ══════════════════════════════════════════════════════════════════════════
        # 2. Locate VRI2 resultant feature class
        # ══════════════════════════════════════════════════════════════════════════
        print('\nWHPOR_11_forDRAT: Finding VRI2 resultant...')
        if not arcpy.Exists(VRI2gdb):
            print(f'ERROR: VRI2 GDB not found at:\n  {VRI2gdb}')
            sys.exit(1)

        arcpy.env.workspace = VRI2gdb
        vri2_list = arcpy.ListFeatureClasses('VRI2_resultant*')
        if not vri2_list:
            print(f'ERROR: No VRI2_resultant* FC found in {VRI2gdb}')
            sys.exit(1)
        vri2_fc = os.path.join(VRI2gdb, vri2_list[0])
        print(f'  VRI2 FC: {vri2_fc}')

        # Verify required VRI fields are present
        vri2_fields = [f.name for f in arcpy.ListFields(vri2_fc)]
        required = ['BEC_ZONE_CODE', 'BEC_SUBZONE', 'MOISTURE_REGIME',
                    'SPECIES_CD_1', 'SPECIES_PCT_1']
        missing_req = [f for f in required if f not in vri2_fields]
        if missing_req:
            print(f'ERROR: VRI2 is missing required fields: {missing_req}')
            sys.exit(1)

        has_variant = 'BEC_VARIANT' in vri2_fields
        if not has_variant:
            print('  WARNING: BEC_VARIANT not found on VRI2. '
                  'BGC key will use zone + subzone only.')

        # ══════════════════════════════════════════════════════════════════════════
        # 3. Calculate per-polygon forDRAT score on VRI2 feature class
        # ══════════════════════════════════════════════════════════════════════════
        print('\nWHPOR_11_forDRAT: Computing per-polygon drought risk scores...')

        arcpy.env.workspace = VRI2gdb

        # Add (or reset) intermediate score field on VRI2
        if arcpy.ListFields(vri2_fc, VRI_SCR_FLD):
            arcpy.management.DeleteField(vri2_fc, VRI_SCR_FLD)
        arcpy.management.AddField(vri2_fc, VRI_SCR_FLD, 'DOUBLE')

        # Build species field list — include only pairs that exist on VRI2
        sp_fields_flat = []
        for i in range(1, 7):
            cd_f  = f'SPECIES_CD_{i}'
            pct_f = f'SPECIES_PCT_{i}'
            if cd_f in vri2_fields and pct_f in vri2_fields:
                sp_fields_flat += [cd_f, pct_f]

        cursor_flds = (['BEC_ZONE_CODE', 'BEC_SUBZONE', 'MOISTURE_REGIME']
                       + (['BEC_VARIANT'] if has_variant else [])
                       + sp_fields_flat
                       + [VRI_SCR_FLD])

        idx_zone  = 0
        idx_sub   = 1
        idx_mr    = 2
        idx_var   = 3 if has_variant else None
        sp_start  = 4 if has_variant else 3
        score_idx = len(cursor_flds) - 1
        n_sp_pairs = len(sp_fields_flat) // 2

        n_scored  = 0
        n_unknown = 0

        with arcpy.da.UpdateCursor(vri2_fc, cursor_flds) as cursor:
            for row in cursor:
                zone    = (row[idx_zone] or '').strip()
                sub     = (row[idx_sub]  or '').strip()
                variant = (row[idx_var]  or '').strip() if has_variant else ''
                bgc     = zone + sub + variant

                mr_raw = row[idx_mr]
                if mr_raw is None:
                    row[score_idx] = None
                    cursor.updateRow(row)
                    n_unknown += 1
                    continue

                smr = VRI_MR_TO_SMR.get(int(mr_raw), None)
                if smr is None:
                    row[score_idx] = None
                    cursor.updateRow(row)
                    n_unknown += 1
                    continue

                total_weighted = 0.0
                total_pct      = 0.0
                for j in range(n_sp_pairs):
                    cd_idx  = sp_start + j * 2
                    pct_idx = sp_start + j * 2 + 1
                    sp_code = (row[cd_idx]  or '').strip().upper()
                    sp_pct  =  row[pct_idx] or 0.0
                    if not sp_code or sp_pct <= 0:
                        continue
                    fordrat_col = VRI_TO_FORDRAT.get(sp_code, None)
                    if fordrat_col is None:
                        continue   # unrecognized species → excluded (unknown)
                    weight = fordrat_lookup.get((bgc, smr, fordrat_col), None)
                    if weight is None:
                        continue   # BGC / SMR combo not covered by forDRAT
                    total_weighted += weight * sp_pct
                    total_pct      += sp_pct

                if total_pct > 0:
                    weighted_avg = total_weighted / total_pct          # 1.0 – 4.0
                    score = round((weighted_avg - 1.0) / 3.0 * 100.0, 2)  # 0 – 100
                    row[score_idx] = score
                    n_scored += 1
                else:
                    row[score_idx] = None
                    n_unknown += 1

                cursor.updateRow(row)

        print(f'  Polygons scored:          {n_scored}')
        print(f'  Unknown / excluded:       {n_unknown}')

        # ══════════════════════════════════════════════════════════════════════════
        # 4. Aggregate scores to each watershed reporting scale
        # ══════════════════════════════════════════════════════════════════════════
        print('\nWHPOR_11_forDRAT: Aggregating scores to watershed reporting units...')

        if not arcpy.Exists(compiled_gdb):
            print(f'ERROR: Compiled GDB not found at:\n  {compiled_gdb}')
            sys.exit(1)

        arcpy.env.workspace = compiled_gdb
        compiled_fcs    = arcpy.ListFeatureClasses('Compiled_Watershed_Features*') or []
        compiled_tables = arcpy.ListTables('Compiled_Watershed_Stats_Table*')      or []
        print(f'  Watershed FCs found:  {compiled_fcs}')
        print(f'  Stats tables found:   {compiled_tables}')

        for ws_fc_name in compiled_fcs:
            ws_fc  = os.path.join(compiled_gdb, ws_fc_name)
            suffix = ws_fc_name.replace('Compiled_Watershed_Features_', '')

            stats_tbl_name = 'Compiled_Watershed_Stats_Table_' + suffix
            stats_tbl = os.path.join(compiled_gdb, stats_tbl_name)
            if not arcpy.Exists(stats_tbl):
                print(f'  WARNING: Stats table "{stats_tbl_name}" not found — '
                      f'skipping scale "{suffix}".')
                continue

            print(f'\n  ── Scale: {suffix} ──')

            # ── 4a. Intersect VRI2 (with per-polygon scores) × watershed polygons ──
            inter_name = 'fordrat_inter_' + suffix
            inter_fc   = os.path.join(compiled_gdb, inter_name)
            if arcpy.Exists(inter_fc):
                arcpy.management.Delete(inter_fc)
            arcpy.analysis.Intersect([vri2_fc, ws_fc], inter_fc, 'NO_FID', '0.1 Meters')
            print(f'    Intersect complete')

            # ── 4b. Add score × area field ────────────────────────────────────────
            if arcpy.ListFields(inter_fc, SCORE_X_AREA):
                arcpy.management.DeleteField(inter_fc, SCORE_X_AREA)
            arcpy.management.AddField(inter_fc, SCORE_X_AREA, 'DOUBLE')

            sxa_codeblock = (
                'def sxa(score, area):\n'
                '    if score is None:\n'
                '        return None\n'
                '    return score * area\n'
            )
            arcpy.management.CalculateField(
                inter_fc, SCORE_X_AREA,
                f'sxa(!{VRI_SCR_FLD}!, !Shape_Area!)',
                'PYTHON3', sxa_codeblock
            )

            # ── 4c. Find RevRepUni on intersect output (may be prefixed after intersect) ──
            rev_candidates = [f.name for f in arcpy.ListFields(inter_fc)
                              if wsLinkFld in f.name]
            if not rev_candidates:
                print(f'    WARNING: {wsLinkFld} not found on intersect output. '
                      f'Skipping scale "{suffix}".')
                arcpy.management.Delete(inter_fc)
                continue
            inter_rev = rev_candidates[0]

            # ── 4d. Summarize: only over non-null scored polygons so that the
            #        area denominator reflects known-species area only ──────────
            summary_name = 'fordrat_sum_' + suffix
            summary_tbl  = os.path.join(compiled_gdb, summary_name)
            if arcpy.Exists(summary_tbl):
                arcpy.management.Delete(summary_tbl)

            # Filter to polygons that have a score before summarizing
            arcpy.management.MakeTableView(
                inter_fc, 'fordrat_scored_view',
                f'{VRI_SCR_FLD} IS NOT NULL'
            )
            arcpy.analysis.Statistics(
                'fordrat_scored_view', summary_tbl,
                [[SCORE_X_AREA, 'SUM'], ['Shape_Area', 'SUM']],
                inter_rev
            )
            arcpy.management.Delete('fordrat_scored_view')

            # ── 4e. Compute weighted score and classify per reporting unit ────────
            arcpy.management.AddField(summary_tbl, SCORE_FIELD, 'DOUBLE')
            arcpy.management.AddField(summary_tbl, CLASS_FIELD, 'TEXT', field_length=10)

            sum_sxa_fld  = 'SUM_' + SCORE_X_AREA
            sum_area_fld = 'SUM_Shape_Area'

            with arcpy.da.UpdateCursor(
                summary_tbl, [sum_sxa_fld, sum_area_fld, SCORE_FIELD, CLASS_FIELD]
            ) as cur:
                for row in cur:
                    s_sxa  = row[0]
                    s_area = row[1]
                    if s_area and s_area > 0 and s_sxa is not None:
                        ws_score = round(s_sxa / s_area, 1)
                        ws_class = classify_score(ws_score)
                    else:
                        ws_score = None
                        ws_class = 'Unknown'
                    row[2] = ws_score
                    row[3] = ws_class
                    cur.updateRow(row)

            # ── 4f. Join SCORE_FIELD and CLASS_FIELD to both the stats table and
            #        the compiled watershed FC (FC needed for map symbology) ────────
            for target in [stats_tbl, ws_fc]:
                # Remove pre-existing drought fields to allow clean re-runs
                for fld in [SCORE_FIELD, CLASS_FIELD]:
                    if arcpy.ListFields(target, fld):
                        try:
                            arcpy.management.DeleteField(target, fld)
                        except Exception:
                            pass

                rev_on_target = [f.name for f in arcpy.ListFields(target)
                                 if wsLinkFld in f.name]
                if not rev_on_target:
                    print(f'    WARNING: {wsLinkFld} not found on '
                          f'{os.path.basename(target)} — skipping join.')
                    continue

                arcpy.management.JoinField(
                    target, rev_on_target[0],
                    summary_tbl, inter_rev,
                    [SCORE_FIELD, CLASS_FIELD]
                )
                print(f'    Joined {SCORE_FIELD}, {CLASS_FIELD} → '
                      f'{os.path.basename(target)}')

            # ── 4g. Clean up temp layers ─────────────────────────────────────────
            arcpy.management.Delete(inter_fc)
            arcpy.management.Delete(summary_tbl)

        print('\n' + '='*60)
        print('WHPOR_11_forDRAT: Complete.')
        print('='*60)
