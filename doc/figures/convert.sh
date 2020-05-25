#! /bin/bash

# First use powerpoint to export the slides to PDF 
# Note: export to PDF, not print to PDF, otherwise trimming will not work.

# figures-positive-disaggregation-feature-guide
magick convert -density 300 -units pixelsperinch -trim +profile "icc" figures-positive-disaggregation-feature-guide.pdf figures-positive-disaggregation-feature-guide.png
mv figures-positive-disaggregation-feature-guide-0.png diagram_clos_3pod_3leaf_3spine_4super.png
mv figures-positive-disaggregation-feature-guide-1.png diagram_clos_3pod_3leaf_3spine_4super_intra_pod_1_failure.png
mv figures-positive-disaggregation-feature-guide-2.png diagram_clos_3pod_3leaf_3spine_4super_inter_pod_1_failure.png
mv figures-positive-disaggregation-feature-guide-3.png diagram_clos_3pod_3leaf_3spine_4super_intra_pod_4_failures.png
