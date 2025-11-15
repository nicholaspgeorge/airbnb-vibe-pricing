#!/bin/bash
# Quick Data Analysis Script - No Python Required
# Uses bash, awk, and basic Unix tools

echo "=========================================================================="
echo "QUICK DATA ANALYSIS - Vibe-Aware Pricing Project"
echo "=========================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Dataset Overview
echo -e "${GREEN}1. DATASET OVERVIEW${NC}"
echo "--------------------------------------------------------------------------"
LISTINGS_ROWS=$(wc -l < listings_London.csv)
echo "Listings rows: $LISTINGS_ROWS"
echo "Listings columns: 79"
echo ""

VIBE_ROWS=$(wc -l < 01_vibe_features_for_modeling.csv)
echo "Vibe features rows: $VIBE_ROWS (neighborhoods)"
echo ""

# 2. Sample Data
echo -e "${GREEN}2. SAMPLE LISTINGS (first 3)${NC}"
echo "--------------------------------------------------------------------------"
head -4 listings_London.csv | tail -3 | cut -d',' -f1,29,34,35,38,41,54 | column -t -s','
echo ""

# 3. Neighbourhood Distribution
echo -e "${GREEN}3. TOP 10 NEIGHBOURHOODS BY LISTING COUNT${NC}"
echo "--------------------------------------------------------------------------"
tail -n +2 listings_London.csv | awk -F',' '{print $29}' | sort | uniq -c | sort -rn | head -10
echo ""

# 4. Room Type Distribution
echo -e "${GREEN}4. ROOM TYPE DISTRIBUTION${NC}"
echo "--------------------------------------------------------------------------"
tail -n +2 listings_London.csv | awk -F',' '{print $34}' | sort | uniq -c | sort -rn
echo ""

# 5. Price Analysis (sample)
echo -e "${GREEN}5. PRICE ANALYSIS (from sample of 1000 listings)${NC}"
echo "--------------------------------------------------------------------------"
tail -n +2 listings_London.csv | head -1000 | awk -F',' '{
    price = $41
    gsub(/\$/, "", price)
    gsub(/,/, "", price)
    if (price > 0 && price < 10000) {
        sum += price
        count++
        if (price < min || min == 0) min = price
        if (price > max) max = price
    }
}
END {
    if (count > 0) {
        print "  Count: " count
        print "  Mean: £" sum/count
        print "  Min: £" min
        print "  Max: £" max
    }
}'
echo ""

# 6. Availability Analysis
echo -e "${GREEN}6. AVAILABILITY FIELDS (sample of 100 listings)${NC}"
echo "--------------------------------------------------------------------------"
tail -n +2 listings_London.csv | head -100 | awk -F',' '{
    a30 = $52
    a60 = $53
    a90 = $54
    a365 = $55

    if (a30 != "") { sum30 += a30; c30++ }
    if (a60 != "") { sum60 += a60; c60++ }
    if (a90 != "") { sum90 += a90; c90++ }
    if (a365 != "") { sum365 += a365; c365++ }
}
END {
    print "  Avg availability_30: " (c30 > 0 ? sum30/c30 : "N/A") " days"
    print "  Avg availability_60: " (c60 > 0 ? sum60/c60 : "N/A") " days"
    print "  Avg availability_90: " (c90 > 0 ? sum90/c90 : "N/A") " days"
    print "  Avg availability_365: " (c365 > 0 ? sum365/c365 : "N/A") " days"
}'
echo ""

# 7. Occupancy Proxy (estimated from sample)
echo -e "${GREEN}7. ESTIMATED OCCUPANCY RATES (from sample)${NC}"
echo "--------------------------------------------------------------------------"
tail -n +2 listings_London.csv | head -1000 | awk -F',' '{
    a90 = $54
    if (a90 != "" && a90 >= 0 && a90 <= 90) {
        occ = 1 - (a90 / 90)
        if (occ >= 0 && occ <= 1) {
            sum_occ += occ
            count++
            if (occ >= 0.75) high_demand++
        }
    }
}
END {
    if (count > 0) {
        print "  Mean occ_90: " sum_occ/count " (" sum_occ/count * 100 "%)"
        print "  High-demand (>=0.75): " high_demand " / " count " (" high_demand/count * 100 "%)"
    }
}'
echo ""

# 8. Vibe Scores Overview
echo -e "${GREEN}8. VIBE SCORES OVERVIEW${NC}"
echo "--------------------------------------------------------------------------"
echo "Top 5 High-Vibe Neighborhoods:"
tail -n +2 01_neighborhood_vibe_scores.csv | sort -t',' -k2 -rn | head -5 | awk -F',' '{print "  " $1 ": " $2}'
echo ""
echo "Bottom 5 Low-Vibe Neighborhoods:"
tail -n +2 01_neighborhood_vibe_scores.csv | sort -t',' -k2 -n | head -5 | awk -F',' '{print "  " $1 ": " $2}'
echo ""

# 9. Vibe Feature Stats
echo -e "${GREEN}9. VIBE FEATURE STATISTICS${NC}"
echo "--------------------------------------------------------------------------"
tail -n +2 01_vibe_features_for_modeling.csv | awk -F',' '{
    vibe += $2
    sent += $3
    walk += $8
    safety += $9
    night += $10
    count++
}
END {
    if (count > 0) {
        print "  Avg vibe_score: " vibe/count
        print "  Avg sentiment: " sent/count
        print "  Avg walkability: " walk/count
        print "  Avg safety: " safety/count
        print "  Avg nightlife: " night/count
    }
}'
echo ""

# 10. Data Quality Check
echo -e "${GREEN}10. DATA QUALITY CHECK${NC}"
echo "--------------------------------------------------------------------------"
echo "Checking for common issues..."

# Check for zero prices
ZERO_PRICES=$(tail -n +2 listings_London.csv | head -10000 | awk -F',' '{
    price = $41
    gsub(/\$/, "", price)
    gsub(/,/, "", price)
    if (price == 0 || price == "") count++
}
END {
    print count
}')
echo "  Listings with \$0 price (in sample): $ZERO_PRICES"

# Check neighbourhood field
NULL_NEIGH=$(tail -n +2 listings_London.csv | head -10000 | awk -F',' '{if ($29 == "") count++} END {print count+0}')
echo "  Listings with null neighbourhood (in sample): $NULL_NEIGH"

echo ""
echo -e "${GREEN}Analysis complete!${NC}"
echo "--------------------------------------------------------------------------"
echo ""
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo "1. Install Python packages (see INSTALL_PACKAGES.md)"
echo "2. Run: python3 test_setup.py"
echo "3. Open: jupyter notebook 00_data_exploration.ipynb"
echo ""
echo "=========================================================================="
