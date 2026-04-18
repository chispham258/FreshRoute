RECIPES = [
    {
        "recipe_id": "R001",
        "name": "Bò xào hành tây cần tỏi",
        "description": "Thịt bò mềm xào cùng hành tây ngọt thanh, thơm mùi tỏi phi.",
        "category": "mon_chinh", "tags": ["thịt bò", "xào", "nhanh"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "thit_bo", "required_qty_g": 150, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "hanh_tay", "required_qty_g": 75, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "toi", "required_qty_g": 10, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "xi_dau", "required_qty_g": 10, "is_optional": True, "role": "seasoning"},
            {"ingredient_id": "tieu", "required_qty_g": 3, "is_optional": True, "role": "spice"}
        ],
        "steps": [
            {"step": 1, "description": "Thịt bò thái mỏng, hành tây cắt múi cau."},
            {"step": 2, "description": "Phi thơm tỏi, cho bò vào xào nhanh tay ở lửa lớn rồi trút ra."},
            {"step": 3, "description": "Xào hành tây chín tới, đổ bò vào lại, nêm xì dầu và tiêu rồi tắt bếp."}
        ],
        "prep_time_minutes": 10, "cook_time_minutes": 5, "total_time_minutes": 15
    },
    {
        "recipe_id": "R002",
        "name": "Sườn heo rim mặn ngọt",
        "description": "Sườn non heo rim vàng óng, vị đậm đà đưa cơm.",
        "category": "mon_chinh", "tags": ["sườn heo", "rim", "mặn ngọt"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "suon_heo", "required_qty_g": 165, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 10, "is_optional": True, "role": "seasoning"},
            {"ingredient_id": "duong", "required_qty_g": 7, "is_optional": True, "role": "seasoning"},
            {"ingredient_id": "hanh_tim", "required_qty_g": 5, "is_optional": True, "role": "aromatic"}
        ],
        "steps": [
            {"step": 1, "description": "Sườn heo chặt nhỏ, luộc sơ để khử mùi."},
            {"step": 2, "description": "Rán sườn vàng các mặt, sau đó cho hành tím băm vào phi thơm."},
            {"step": 3, "description": "Hòa hỗn hợp nước mắm đường rưới vào chảo, rim lửa nhỏ đến khi sệt lại."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 25, "total_time_minutes": 40
    },
    {
        "recipe_id": "R003",
        "name": "Thịt heo xay chưng trứng",
        "description": "Món ăn mềm mại, giàu dinh dưỡng, phù hợp cho cả trẻ nhỏ.",
        "category": "mon_chinh", "tags": ["thịt heo", "trứng", "hấp"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "thit_heo_xay", "required_qty_g": 100, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "trung_ga", "required_qty_g": 60, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "hanh_la", "required_qty_g": 5, "is_optional": True, "role": "garnish"},
            {"ingredient_id": "muoi", "required_qty_g": 3, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Đập trứng vào bát thịt xay, nêm muối và hành lá rồi đánh tan."},
            {"step": 2, "description": "Đem bát hỗn hợp đi hấp cách thủy trong khoảng 15-20 phút."},
            {"step": 3, "description": "Kiểm tra thịt chín bằng tăm, dùng nóng với cơm trắng."}
        ],
        "prep_time_minutes": 5, "cook_time_minutes": 20, "total_time_minutes": 25
    },
    {
        "recipe_id": "R004",
        "name": "Thịt ba chỉ luộc",
        "description": "Thịt heo sáp luộc chín tới, trắng giòn, chấm nước mắm tỏi ớt.",
        "category": "mon_chinh", "tags": ["thịt heo", "luộc", "truyền thống"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "heo_sap", "required_qty_g": 165, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "gung", "required_qty_g": 3, "is_optional": True, "role": "cleaning"},
            {"ingredient_id": "hanh_tim", "required_qty_g": 3, "is_optional": True, "role": "cleaning"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 7, "is_optional": True, "role": "dipping_sauce"}
        ],
        "steps": [
            {"step": 1, "description": "Thịt ba chỉ rửa sạch. Đun nước sôi với gừng và hành tím đập dập."},
            {"step": 2, "description": "Cho thịt vào luộc khoảng 20-25 phút cho đến khi chín đều."},
            {"step": 3, "description": "Vớt thịt ra để nguội bớt, thái lát mỏng vừa ăn."}
        ],
        "prep_time_minutes": 5, "cook_time_minutes": 25, "total_time_minutes": 30
    },
    {
        "recipe_id": "R005",
        "name": "Cánh gà chiên nước mắm",
        "description": "Cánh gà giòn rụm bám đều lớp sốt mặn ngọt cay nhẹ.",
        "category": "mon_chinh", "tags": ["gà", "chiên", "ăn chơi"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "canh_ga", "required_qty_g": 200, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 20, "is_optional": True, "role": "seasoning"},
            {"ingredient_id": "duong", "required_qty_g": 15, "is_optional": True, "role": "seasoning"},
            {"ingredient_id": "toi", "required_qty_g": 8, "is_optional": True, "role": "aromatic"}
        ],
        "steps": [
            {"step": 1, "description": "Cánh gà rửa sạch, chiên vàng giòn các mặt."},
            {"step": 2, "description": "Phi tỏi băm, cho nước mắm và đường vào đun sệt lại."},
            {"step": 3, "description": "Cho gà vào đảo nhanh tay để nước sốt bám đều."}
        ],
        "prep_time_minutes": 10, "cook_time_minutes": 20, "total_time_minutes": 30
    },
    {
        "recipe_id": "R006",
        "name": "Canh khổ qua thịt bằm",
        "description": "Món canh thanh nhiệt giải độc, nước dùng ngọt thanh từ thịt xay.",
        "category": "canh", "tags": ["khổ qua", "thịt heo", "thanh nhiệt"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "kho_qua", "required_qty_g": 100, "is_optional": False, "role": "main_vegetable"},
            {"ingredient_id": "thit_heo_xay", "required_qty_g": 50, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "hanh_la", "required_qty_g": 3, "is_optional": True, "role": "garnish"},
            {"ingredient_id": "hat_nem", "required_qty_g": 3, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Khổ qua bỏ ruột thái lát. Đun sôi nước."},
            {"step": 2, "description": "Cho thịt xay vào nấu lấy nước ngọt, vớt bọt."},
            {"step": 3, "description": "Cho khổ qua vào nấu chín tới, nêm hạt nêm và hành lá."}
        ],
        "prep_time_minutes": 10, "cook_time_minutes": 15, "total_time_minutes": 25
    },
    {
        "recipe_id": "R007",
        "name": "Cá lóc phi lê kho tộ",
        "description": "Cá lóc phi lê không xương, kho đậm đà trong niêu đất.",
        "category": "mon_chinh", "tags": ["cá lóc", "kho", "miền tây"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ca_loc", "required_qty_g": 200, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "hanh_la", "required_qty_g": 5, "is_optional": True, "role": "garnish"},
            {"ingredient_id": "ot_chuong", "required_qty_g": 25, "is_optional": True, "role": "vegetable"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 15, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Cá lóc ướp nước mắm, nước màu hành tím."},
            {"step": 2, "description": "Kho lửa nhỏ cho cá thấm vị."},
            {"step": 3, "description": "Thêm ớt chuông thái miếng (nếu có) và hành lá khi nước gần cạn."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 20, "total_time_minutes": 35
    },
    {
        "recipe_id": "R008",
        "name": "Rau muống xào tỏi",
        "description": "Rau muống xanh mướt, giòn sần sật và thơm mùi tỏi đặc trưng.",
        "category": "mon_phu", "tags": ["rau muống", "xào", "nhanh"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "rau_muong", "required_qty_g": 150, "is_optional": False, "role": "main_vegetable"},
            {"ingredient_id": "toi", "required_qty_g": 15, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "dau_an", "required_qty_g": 10, "is_optional": True, "role": "cooking_fat"},
            {"ingredient_id": "hat_nem", "required_qty_g": 3, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Rau muống nhặt sạch. Tỏi đập dập."},
            {"step": 2, "description": "Phi thơm tỏi với dầu ăn, cho rau vào xào lửa thật lớn."},
            {"step": 3, "description": "Rau vừa chín tới, nêm hạt nêm rồi trút ra đĩa ngay."}
        ],
        "prep_time_minutes": 5, "cook_time_minutes": 5, "total_time_minutes": 10
    },
    {
        "recipe_id": "R009",
        "name": "Canh chua cá ba sa",
        "description": "Vị chua từ me, ngọt béo từ cá ba sa tạo nên món canh hấp dẫn.",
        "category": "canh", "tags": ["cá ba sa", "canh chua", "đặc sản"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ca_ba_sa", "required_qty_g": 165, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "ca_chua", "required_qty_g": 35, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "me", "required_qty_g": 10, "is_optional": False, "role": "seasoning_base"},
            {"ingredient_id": "khom", "required_qty_g": 35, "is_optional": True, "role": "vegetable"}
        ],
        "steps": [
            {"step": 1, "description": "Cá ba sa rửa sạch, cà chua bổ múi cau, khóm thái miếng."},
            {"step": 2, "description": "Dầm me lấy nước chua, đun sôi rồi cho cá vào nấu chín."},
            {"step": 3, "description": "Cho cà chua, khóm vào đun sôi lại, nêm mắm đường cho vừa vị chua ngọt."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 15, "total_time_minutes": 30
    },
    {
        "recipe_id": "R010",
        "name": "Nghêu hấp sả",
        "description": "Nghêu tươi ngọt nước, mùi sả nồng nàn thơm phức.",
        "category": "khai_vi", "tags": ["nghêu", "hải sản", "hấp"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ngheu", "required_qty_g": 250, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "sa", "required_qty_g": 15, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "tuong_ot", "required_qty_g": 5, "is_optional": True, "role": "dipping"}
        ],
        "steps": [
            {"step": 1, "description": "Nghêu ngâm rửa sạch. Sả đập dập cắt khúc."},
            {"step": 2, "description": "Lót sả xuống đáy nồi, cho nghêu lên trên với chút nước."},
            {"step": 3, "description": "Đun sôi đến khi nghêu há miệng hoàn toàn thì tắt bếp."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 10, "total_time_minutes": 30
    },
    {
        "recipe_id": "R011",
        "name": "Phở bò truyền thống",
        "description": "Bánh phở tươi mềm mượt kết hợp với thịt bò thăn thái mỏng và nước dùng đậm đà.",
        "category": "mon_chinh", "tags": ["phở", "thịt bò", "ăn sáng"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "banh_pho", "required_qty_g": 250, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "thit_bo", "required_qty_g": 100, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "nuoc_ham_xuong", "required_qty_g": 250, "is_optional": False, "role": "base_broth"},
            {"ingredient_id": "hanh_la", "required_qty_g": 10, "is_optional": True, "role": "garnish"},
            {"ingredient_id": "gung", "required_qty_g": 5, "is_optional": True, "role": "aromatic"}
        ],
        "steps": [
            {"step": 1, "description": "Nấu sôi nước hầm xương với gừng nướng thơm."},
            {"step": 2, "description": "Chần bánh phở qua nước sôi, xếp vào bát cùng thịt bò thái mỏng."},
            {"step": 3, "description": "Chan nước dùng đang sôi sùng sục vào bát để thịt bò chín tái, thêm hành lá."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 10, "total_time_minutes": 25
    },
    {
        "recipe_id": "R012",
        "name": "Mì gói xào bò ớt chuông",
        "description": "Bữa tối nhanh gọn với mì Omachi xào thịt bò và ớt chuông giòn ngọt.",
        "category": "mon_chinh", "tags": ["mì gói", "thịt bò", "nhanh"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "mi_goi", "required_qty_g": 80, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "thit_bo", "required_qty_g": 100, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "ot_chuong", "required_qty_g": 100, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "toi", "required_qty_g": 10, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "dau_an", "required_qty_g": 10, "is_optional": True, "role": "cooking_fat"}
        ],
        "steps": [
            {"step": 1, "description": "Chần mì gói sơ qua rồi vớt ra ráo nước. Thịt bò và ớt chuông thái sợi."},
            {"step": 2, "description": "Phi tỏi, xào thịt bò nhanh tay rồi cho ớt chuông vào đảo cùng."},
            {"step": 3, "description": "Cho mì vào chảo, nêm gói gia vị mì, đảo đều cho thấm rồi tắt bếp."}
        ],
        "prep_time_minutes": 5, "cook_time_minutes": 7, "total_time_minutes": 12
    },
    {
        "recipe_id": "R013",
        "name": "Bún tươi trộn tôm thịt",
        "description": "Món trộn thanh mát với bún gói, tôm sú và thịt heo sáp luộc.",
        "category": "mon_chinh", "tags": ["bún", "tôm", "thanh mát"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "bun_tuong", "required_qty_g": 200, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "tom", "required_qty_g": 75, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "heo_sap", "required_qty_g": 50, "is_optional": False, "role": "protein"},
            {"ingredient_id": "rau_muong", "required_qty_g": 50, "is_optional": True, "role": "vegetable"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 10, "is_optional": True, "role": "dressing"}
        ],
        "steps": [
            {"step": 1, "description": "Luộc chín tôm và thịt ba chỉ, tôm lột vỏ, thịt thái mỏng."},
            {"step": 2, "description": "Luộc rau muống chẻ nhỏ để làm rau ăn kèm."},
            {"step": 3, "description": "Cho bún vào bát, xếp tôm thịt lên trên, trộn cùng nước mắm chua ngọt."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 15, "total_time_minutes": 35
    },
    {
        "recipe_id": "R014",
        "name": "Mì Ý sốt bò bằm cà chua",
        "description": "Mì Spaghetti dai ngon quyện trong sốt cà chua và thịt bò xay.",
        "category": "mon_chinh", "tags": ["mì ý", "thịt bò", "trẻ em"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "mi_y", "required_qty_g": 100, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "thit_heo_xay", "required_qty_g": 50, "is_optional": False, "role": "protein"},
            {"ingredient_id": "thit_bo", "required_qty_g": 50, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "ca_chua", "required_qty_g": 100, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "hanh_tay", "required_qty_g": 25, "is_optional": True, "role": "aromatic"}
        ],
        "steps": [
            {"step": 1, "description": "Luộc mì Ý theo thời gian trên bao bì. Thịt bò băm nhỏ trộn với thịt heo xay."},
            {"step": 2, "description": "Xào hành tây và cà chua băm nhuyễn thành sốt, cho thịt vào xào chín."},
            {"step": 3, "description": "Trộn mì vào sốt, nêm chút hạt nêm và đường cho vừa vị."}
        ],
        "prep_time_minutes": 10, "cook_time_minutes": 20, "total_time_minutes": 30
    },
    {
        "recipe_id": "R015",
        "name": "Mực xào hành tây cần tỏi",
        "description": "Mực ống tươi giòn xào cùng hành tây, món nhắm hoặc ăn cơm đều ngon.",
        "category": "mon_chinh", "tags": ["mực", "hải sản", "xào"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "muc", "required_qty_g": 150, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "hanh_tay", "required_qty_g": 75, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "toi", "required_qty_g": 8, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "hanh_la", "required_qty_g": 5, "is_optional": True, "role": "garnish"}
        ],
        "steps": [
            {"step": 1, "description": "Mực làm sạch, khía hoa hoặc thái miếng vừa ăn. Hành tây cắt múi cau."},
            {"step": 2, "description": "Phi thơm tỏi, cho mực vào xào lửa lớn để không ra nước."},
            {"step": 3, "description": "Cho hành tây vào đảo nhanh, nêm chút nước mắm và tiêu rồi tắt bếp."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 7, "total_time_minutes": 22
    },
    {
        "recipe_id": "R016",
        "name": "Gà ta kho gừng",
        "description": "Thịt gà ta chắc ngọt, thơm nồng vị gừng tươi, rất ấm bụng.",
        "category": "mon_chinh", "tags": ["gà ta", "kho", "gia đình"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ga_nguyen_con", "required_qty_g": 375, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "gung", "required_qty_g": 13, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 13, "is_optional": True, "role": "seasoning"},
            {"ingredient_id": "hanh_tim", "required_qty_g": 5, "is_optional": True, "role": "aromatic"}
        ],
        "steps": [
            {"step": 1, "description": "Gà ta chặt miếng vừa ăn. Gừng thái sợi."},
            {"step": 2, "description": "Phi thơm hành tím và một nửa phần gừng, cho gà vào xào săn."},
            {"step": 3, "description": "Cho nước mắm, đường và phần gừng còn lại vào, kho lửa nhỏ đến khi gà chín mềm, nước sệt."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 30, "total_time_minutes": 50
    },
    {
        "recipe_id": "R017",
        "name": "Vịt kho sả ớt",
        "description": "Thịt vịt tươi kho với sả băm và sa tế cay nồng đậm đà.",
        "category": "mon_chinh", "tags": ["thịt vịt", "kho", "cay"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "thit_vit", "required_qty_g": 165, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "sa", "required_qty_g": 15, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "sa_te", "required_qty_g": 7, "is_optional": True, "role": "spice"},
            {"ingredient_id": "gung", "required_qty_g": 7, "is_optional": True, "role": "cleaning"}
        ],
        "steps": [
            {"step": 1, "description": "Dùng gừng và rượu bóp thịt vịt để khử mùi, sau đó chặt miếng nhỏ."},
            {"step": 2, "description": "Ướp vịt với sả băm, sa tế và gia vị trong 15 phút."},
            {"step": 3, "description": "Xào vịt cho ra bớt mỡ, sau đó kho nhỏ lửa đến khi thịt vịt mềm và thấm vị."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 35, "total_time_minutes": 55
    },
    {
        "recipe_id": "R018",
        "name": "Cá rô phi chiên xù",
        "description": "Cá rô phi chiên vàng giòn lớp vỏ, thịt bên trong ngọt lịm.",
        "category": "mon_chinh", "tags": ["cá rô phi", "chiên", "giòn"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ca_ro", "required_qty_g": 250, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "bot_mi", "required_qty_g": 50, "is_optional": True, "role": "coating"},
            {"ingredient_id": "dau_an", "required_qty_g": 100, "is_optional": True, "role": "cooking_fat"},
            {"ingredient_id": "chanh", "required_qty_g": 10, "is_optional": True, "role": "dipping"}
        ],
        "steps": [
            {"step": 1, "description": "Cá rô phi làm sạch, để ráo nước. Có thể khứa nhẹ trên thân cá."},
            {"step": 2, "description": "Phủ một lớp mỏng bột mì lên cá để khi chiên không bị bắn dầu và giòn hơn."},
            {"step": 3, "description": "Chiên cá ngập dầu đến khi vàng đều hai mặt. Dùng nóng với nước mắm chanh tỏi ớt."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 15, "total_time_minutes": 30
    },
    {
        "recipe_id": "R019",
        "name": "Canh cá chép nấu dưa cải",
        "description": "Vị chua đặc trưng của dưa cải hòa quyện với vị ngọt của cá chép.",
        "category": "canh", "tags": ["cá chép", "dưa cải", "canh chua"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ca_chep", "required_qty_g": 165, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "dua_cai", "required_qty_g": 100, "is_optional": False, "role": "main_vegetable"},
            {"ingredient_id": "ca_chua", "required_qty_g": 35, "is_optional": True, "role": "vegetable"},
            {"ingredient_id": "hanh_la", "required_qty_g": 3, "is_optional": True, "role": "garnish"}
        ],
        "steps": [
            {"step": 1, "description": "Cá chép làm sạch, chiên sơ cho săn thịt. Dưa cải rửa qua nước cho bớt mặn."},
            {"step": 2, "description": "Xào cà chua và dưa cải, sau đó đổ nước vào đun sôi."},
            {"step": 3, "description": "Cho cá vào nấu chung khoảng 15 phút, nêm nếm lại gia vị rồi rắc hành lá."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 20, "total_time_minutes": 35
    },
    {
        "recipe_id": "R020",
        "name": "Cá hồng hấp xì dầu",
        "description": "Món hấp thanh tao, giữ trọn vị ngọt của cá hồng cùng hương vị xì dầu thơm đặc trưng.",
        "category": "mon_chinh", "tags": ["cá hồng", "hấp", "thanh đạm"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ca_hong", "required_qty_g": 200, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "xi_dau", "required_qty_g": 25, "is_optional": False, "role": "seasoning_base"},
            {"ingredient_id": "gung", "required_qty_g": 10, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "hanh_la", "required_qty_g": 8, "is_optional": True, "role": "garnish"}
        ],
        "steps": [
            {"step": 1, "description": "Cá hồng làm sạch, khứa nhẹ thân cá. Gừng và hành lá thái sợi."},
            {"step": 2, "description": "Đặt cá vào đĩa hấp, rưới xì dầu đều lên mình cá và xếp gừng lên trên."},
            {"step": 3, "description": "Hấp cách thủy khoảng 15-20 phút. Khi cá chín, thêm hành lá và thưởng thức."}
        ],
        "prep_time_minutes": 10, "cook_time_minutes": 20, "total_time_minutes": 30
    },
    {
        "recipe_id": "R021",
        "name": "Lòng heo xào dưa cải chua",
        "description": "Lòng heo dai giòn xào cùng dưa cải chua thanh, món nhắm cực kỳ bắt miệng.",
        "category": "mon_chinh", "tags": ["lòng heo", "dưa cải", "món nhắm"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "long_heo", "required_qty_g": 135, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "dua_cai", "required_qty_g": 100, "is_optional": False, "role": "main_vegetable"},
            {"ingredient_id": "ca_chua", "required_qty_g": 35, "is_optional": True, "role": "vegetable"},
            {"ingredient_id": "hanh_la", "required_qty_g": 3, "is_optional": True, "role": "garnish"}
        ],
        "steps": [
            {"step": 1, "description": "Lòng heo làm sạch, luộc sơ với gừng rồi thái miếng. Dưa cải cắt khúc."},
            {"step": 2, "description": "Xào thơm hành tím, cho lòng vào xào săn với chút nước mắm."},
            {"step": 3, "description": "Cho dưa cải và cà chua vào đảo chung đến khi chín tới, rắc hành lá và tiêu."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 10, "total_time_minutes": 30
    },
    {
        "recipe_id": "R022",
        "name": "Canh giò heo hầm bí đỏ",
        "description": "Món canh bổ dưỡng, giò heo béo ngậy hầm cùng bí đỏ bùi ngọt.",
        "category": "canh", "tags": ["giò heo", "bí đỏ", "bổ dưỡng"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "gio_heo", "required_qty_g": 200, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "bi_do", "required_qty_g": 125, "is_optional": False, "role": "main_vegetable"},
            {"ingredient_id": "hanh_la", "required_qty_g": 4, "is_optional": True, "role": "garnish"},
            {"ingredient_id": "hat_nem", "required_qty_g": 4, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Giò heo chặt miếng, chần nước sôi. Bí đỏ gọt vỏ, cắt miếng vuông."},
            {"step": 2, "description": "Ninh giò heo với nước lọc khoảng 30-40 phút cho mềm."},
            {"step": 3, "description": "Cho bí đỏ vào nấu cùng đến khi bí chín mềm, nêm hạt nêm và hành lá."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 45, "total_time_minutes": 60
    },
    {
        "recipe_id": "R023",
        "name": "Chả giò chiên giòn rụm",
        "description": "Chả giò đông lạnh tiện lợi, chiên vàng đều ăn kèm rau sống.",
        "category": "mon_chinh", "tags": ["chả giò", "chiên", "nhanh"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "cha_gio", "required_qty_g": 150, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "dau_an", "required_qty_g": 100, "is_optional": False, "role": "cooking_fat"},
            {"ingredient_id": "tuong_ot", "required_qty_g": 10, "is_optional": True, "role": "dipping"}
        ],
        "steps": [
            {"step": 1, "description": "Để chả giò rã đông tự nhiên khoảng 5-10 phút."},
            {"step": 2, "description": "Đun nóng dầu ăn, cho chả giò vào chiên ở lửa vừa."},
            {"step": 3, "description": "Lật đều tay đến khi lớp vỏ vàng giòn, vớt ra thấm dầu và chấm tương ớt."}
        ],
        "prep_time_minutes": 5, "cook_time_minutes": 10, "total_time_minutes": 15
    },
    {
        "recipe_id": "R024",
        "name": "Bún đậu mắm tôm (Kiểu đơn giản)",
        "description": "Tận dụng bún đậu gói và đậu hũ trắng cùng thịt ba chỉ luộc.",
        "category": "mon_chinh", "tags": ["bún đậu", "thịt heo", "đặc sản"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "bun_dau", "required_qty_g": 200, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "dau_hu", "required_qty_g": 150, "is_optional": False, "role": "protein"},
            {"ingredient_id": "heo_sap", "required_qty_g": 100, "is_optional": True, "role": "protein"},
            {"ingredient_id": "chanh", "required_qty_g": 10, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Đậu hũ cắt khối vuông, chiên vàng giòn các mặt."},
            {"step": 2, "description": "Thịt ba chỉ (heo sáp) luộc chín, thái lát mỏng. Chần bún đậu qua nước sôi."},
            {"step": 3, "description": "Bày tất cả ra đĩa, dùng kèm mắm tôm pha chanh đường ớt."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 15, "total_time_minutes": 30
    },
    {
        "recipe_id": "R025",
        "name": "Gỏi bánh tráng trộn tôm thịt",
        "description": "Bánh tráng cuốn cắt nhỏ trộn cùng tôm, thịt và rau muống chẻ.",
        "category": "khai_vi", "tags": ["bánh tráng", "tôm", "ăn chơi"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "banh_trang", "required_qty_g": 50, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "tom", "required_qty_g": 50, "is_optional": False, "role": "protein"},
            {"ingredient_id": "rau_muong", "required_qty_g": 25, "is_optional": True, "role": "vegetable"},
            {"ingredient_id": "sa_te", "required_qty_g": 5, "is_optional": True, "role": "spice"}
        ],
        "steps": [
            {"step": 1, "description": "Bánh tráng cắt sợi dài vừa ăn. Tôm luộc chín, bóc vỏ."},
            {"step": 2, "description": "Rau muống lấy phần thân non chẻ sợi nhỏ."},
            {"step": 3, "description": "Trộn bánh tráng với tôm, rau muống, sa tế và nước mắm chua ngọt cho thấm đều."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 5, "total_time_minutes": 25
    },
    {
        "recipe_id": "R026",
        "name": "Bún cá rô đồng",
        "description": "Thịt cá rô đồng ngọt thơm, nước dùng trong vắt, ăn kèm rau cải xanh.",
        "category": "mon_an_sang", "tags": ["bún cá", "cá rô", "dân dã"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ca_ro", "required_qty_g": 125, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "bun_tuong", "required_qty_g": 150, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "cai_xanh", "required_qty_g": 50, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "gung", "required_qty_g": 5, "is_optional": True, "role": "aromatic"}
        ],
        "steps": [
            {"step": 1, "description": "Cá rô làm sạch, luộc chín với gừng. Gỡ lấy thịt cá, phần xương giã nhỏ lọc lấy nước dùng."},
            {"step": 2, "description": "Thịt cá rô đem chiên vàng hoặc xào săn với hành tím."},
            {"step": 3, "description": "Đun sôi nước dùng, cho bún và rau cải xanh vào bát, xếp cá lên trên rồi chan nước."}
        ],
        "prep_time_minutes": 30, "cook_time_minutes": 25, "total_time_minutes": 55
    },
    {
        "recipe_id": "R027",
        "name": "Cháo lòng heo",
        "description": "Cháo gạo tẻ nấu cùng lòng heo và tiết heo bổ dưỡng.",
        "category": "mon_chinh", "tags": ["cháo", "lòng heo", "truyền thống"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "long_heo", "required_qty_g": 100, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "thit_heo_xay", "required_qty_g": 25, "is_optional": True, "role": "protein"},
            {"ingredient_id": "hanh_la", "required_qty_g": 5, "is_optional": True, "role": "garnish"},
            {"ingredient_id": "gung", "required_qty_g": 3, "is_optional": True, "role": "aromatic"}
        ],
        "steps": [
            {"step": 1, "description": "Lòng heo làm sạch với muối và gừng, luộc chín rồi thái miếng vừa ăn."},
            {"step": 2, "description": "Gạo tẻ rang sơ rồi nấu cháo cho đến khi hạt gạo nở mềm."},
            {"step": 3, "description": "Cho lòng heo đã thái vào bát, múc cháo nóng đè lên, rắc hành lá và tiêu bột."}
        ],
        "prep_time_minutes": 25, "cook_time_minutes": 45, "total_time_minutes": 70
    },
    {
        "recipe_id": "R028",
        "name": "Bún bò Huế (Kiểu nhanh)",
        "description": "Hương vị cay nồng đặc trưng với bún tươi, bắp bò và sả.",
        "category": "mon_chinh", "tags": ["bún bò", "cay", "đặc sản"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "thit_bo", "required_qty_g": 100, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "bun_tuong", "required_qty_g": 150, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "sa", "required_qty_g": 25, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "sa_te", "required_qty_g": 5, "is_optional": True, "role": "spice"}
        ],
        "steps": [
            {"step": 1, "description": "Thịt bò thái mỏng. Sả đập dập, một phần băm nhỏ."},
            {"step": 2, "description": "Nấu nước dùng với sả và gia vị bún bò. Phi thơm sả băm với sa tế cho vào nồi nước."},
            {"step": 3, "description": "Chần bún và thịt bò, cho vào tô rồi chan nước dùng nóng hổi."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 40, "total_time_minutes": 60
    },
    {
        "recipe_id": "R029",
        "name": "Canh cua đồng rau muống",
        "description": "Bát canh giải nhiệt với gạch cua béo ngậy và rau muống giòn.",
        "category": "canh", "tags": ["canh cua", "rau muống", "giải nhiệt"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "cua_dong", "required_qty_g": 100, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "rau_muong", "required_qty_g": 65, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "hanh_tim", "required_qty_g": 3, "is_optional": True, "role": "aromatic"}
        ],
        "steps": [
            {"step": 1, "description": "Cua đồng xay lọc lấy nước, đun lửa nhỏ cho thịt cua kết tảng."},
            {"step": 2, "description": "Rau muống nhặt sạch, cắt khúc vừa ăn."},
            {"step": 3, "description": "Khi nước cua sôi, cho rau muống vào nấu chín, nêm gia vị vừa ăn rồi tắt bếp."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 10, "total_time_minutes": 25
    },
    {
        "recipe_id": "R030",
        "name": "Mì Ý hải sản (Tôm mực)",
        "description": "Sự kết hợp giữa mì Ý dai ngon với tôm và mực ống tươi.",
        "category": "mon_chinh", "tags": ["mì ý", "hải sản", "hiện đại"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "mi_y", "required_qty_g": 100, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "tom", "required_qty_g": 50, "is_optional": False, "role": "protein"},
            {"ingredient_id": "muc", "required_qty_g": 50, "is_optional": False, "role": "protein"},
            {"ingredient_id": "ca_chua", "required_qty_g": 75, "is_optional": False, "role": "sauce_base"}
        ],
        "steps": [
            {"step": 1, "description": "Luộc mì Ý. Tôm lột vỏ, mực thái khoanh tròn."},
            {"step": 2, "description": "Xào thơm tỏi, cho hải sản vào đảo nhanh tay rồi để riêng."},
            {"step": 3, "description": "Làm sốt cà chua, cho mì và hải sản vào trộn đều cho thấm vị."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 15, "total_time_minutes": 30
    },
    {
        "recipe_id": "R031",
        "name": "Cá lóc kho tộ",
        "description": "Món cá kho đậm đà, màu sắc bắt mắt, vị mặn ngọt hài hòa đặc trưng miền Tây.",
        "category": "mon_chinh", "tags": ["cá lóc", "kho", "gia đình"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ca_loc", "required_qty_g": 135, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "heo_sap", "required_qty_g": 35, "is_optional": True, "role": "fat_source"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 13, "is_optional": True, "role": "seasoning"},
            {"ingredient_id": "ot_chuong", "required_qty_g": 10, "is_optional": True, "role": "spice"},
            {"ingredient_id": "hanh_la", "required_qty_g": 5, "is_optional": True, "role": "garnish"}
        ],
        "steps": [
            {"step": 1, "description": "Cá lóc làm sạch, cắt khoanh. Thịt ba chỉ (heo sáp) thái miếng nhỏ."},
            {"step": 2, "description": "Ướp cá với nước mắm, đường, nước màu và hành tím băm trong 20 phút."},
            {"step": 3, "description": "Cho thịt ba chỉ vào nồi kho trước cho ra mỡ, xếp cá lên trên, kho lửa nhỏ đến khi nước sệt lại."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 25, "total_time_minutes": 45
    },
    {
        "recipe_id": "R032",
        "name": "Canh chua cá lóc",
        "description": "Món canh quốc hồn quốc túy với vị chua của me và vị ngọt của cá lóc phi lê.",
        "category": "canh", "tags": ["cá lóc", "canh chua", "miền tây"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ca_loc", "required_qty_g": 100, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "ca_chua", "required_qty_g": 25, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "khom", "required_qty_g": 40, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "me", "required_qty_g": 8, "is_optional": False, "role": "seasoning_base"},
            {"ingredient_id": "bac_ha", "required_qty_g": 25, "is_optional": True, "role": "vegetable"}
        ],
        "steps": [
            {"step": 1, "description": "Cá lóc phi lê cắt miếng. Cà chua và khóm sơ chế vừa ăn."},
            {"step": 2, "description": "Nấu sôi nước me, cho cá vào nấu chín rồi vớt bọt."},
            {"step": 3, "description": "Cho cà chua, khóm vào đun sôi, nêm mắm đường cho vừa vị chua ngọt rồi rắc rau thơm."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 15, "total_time_minutes": 35
    },
    {
        "recipe_id": "R033",
        "name": "Sườn heo xào chua ngọt",
        "description": "Sườn non chiên vàng, thấm sốt cà chua và hành tây chua ngọt.",
        "category": "mon_chinh", "tags": ["sườn heo", "chua ngọt", "trẻ em"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "suon_heo", "required_qty_g": 165, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "ca_chua", "required_qty_g": 35, "is_optional": False, "role": "sauce_base"},
            {"ingredient_id": "hanh_tay", "required_qty_g": 15, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "chanh", "required_qty_g": 3, "is_optional": True, "role": "acid_source"}
        ],
        "steps": [
            {"step": 1, "description": "Sườn heo chặt nhỏ, luộc sơ rồi chiên vàng đều."},
            {"step": 2, "description": "Xào hành tây và cà chua băm nhỏ để tạo hỗn hợp sốt sệt."},
            {"step": 3, "description": "Cho sườn vào sốt, nêm đường, nước mắm và nước cốt chanh cho vừa vị chua ngọt."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 20, "total_time_minutes": 35
    },
    {
        "recipe_id": "R034",
        "name": "Thịt kho tàu (Trứng vịt)",
        "description": "Thịt heo ba chỉ kho cùng trứng vịt và nước dừa đóng hộp thanh ngọt.",
        "category": "mon_chinh", "tags": ["thịt heo", "trứng vịt", "tết"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "heo_sap", "required_qty_g": 125, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "trung_vit", "required_qty_g": 1, "is_optional": False, "role": "protein"},
            {"ingredient_id": "nuoc_dua", "required_qty_g": 100, "is_optional": False, "role": "liquid"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 13, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Thịt ba chỉ thái miếng vuông lớn. Trứng vịt luộc chín, bóc vỏ."},
            {"step": 2, "description": "Ướp thịt với nước mắm, hành tím. Sau đó cho vào nồi đảo săn."},
            {"step": 3, "description": "Đổ nước dừa đóng hộp vào ngập thịt, cho trứng vào kho lửa nhỏ đến khi thịt mềm."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 60, "total_time_minutes": 80
    },
    {
        "recipe_id": "R035",
        "name": "Bún riêu cua đồng (Kiểu đơn giản)",
        "description": "Tận dụng cua đồng tươi nấu cùng cà chua và đậu hũ trắng.",
        "category": "mon_chinh", "tags": ["bún riêu", "cua đồng", "dân dã"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "cua_dong", "required_qty_g": 100, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "bun_tuong", "required_qty_g": 135, "is_optional": False, "role": "main_carb"},
            {"ingredient_id": "dau_hu", "required_qty_g": 65, "is_optional": False, "role": "protein"},
            {"ingredient_id": "ca_chua", "required_qty_g": 50, "is_optional": True, "role": "vegetable"}
        ],
        "steps": [
            {"step": 1, "description": "Cua đồng xay lọc lấy nước. Đậu hũ cắt nhỏ chiên vàng."},
            {"step": 2, "description": "Nấu nước cua cho nổi riêu, sau đó cho cà chua xào thơm và đậu hũ chiên vào."},
            {"step": 3, "description": "Chan nước dùng vào tô bún tươi, thêm chút mắm tôm và chanh nếu có."}
        ],
        "prep_time_minutes": 20, "cook_time_minutes": 20, "total_time_minutes": 40
    },
    {
        "recipe_id": "R036",
        "name": "Salad ức gà Healthy",
        "description": "Món ăn thanh nhẹ, giàu protein từ thịt gà công nghiệp và rau củ tươi.",
        "category": "mon_phu", "tags": ["healthy", "ức gà", "salad"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "ga_indonesia", "required_qty_g": 150, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "ca_chua", "required_qty_g": 50, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "dua_leo", "required_qty_g": 50, "is_optional": True, "role": "vegetable"},
            {"ingredient_id": "chanh", "required_qty_g": 10, "is_optional": True, "role": "dressing_base"}
        ],
        "steps": [
            {"step": 1, "description": "Gà công nghiệp (lấy phần ức) luộc chín với chút muối, để nguội rồi xé phay hoặc thái miếng."},
            {"step": 2, "description": "Cà chua và dưa leo rửa sạch, thái lát vừa ăn."},
            {"step": 3, "description": "Trộn gà và rau củ với nước cốt chanh, chút đường và tiêu cho thấm vị."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 10, "total_time_minutes": 25
    },
    {
        "recipe_id": "R037",
        "name": "Gà kho sả ớt",
        "description": "Thịt đùi gà dai giòn, thơm nồng mùi sả và vị cay của sa tế.",
        "category": "mon_chinh", "tags": ["thịt gà", "kho", "cay"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "thit_ga", "required_qty_g": 165, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "sa", "required_qty_g": 15, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "sa_te", "required_qty_g": 5, "is_optional": True, "role": "spice"},
            {"ingredient_id": "nuoc_mam", "required_qty_g": 10, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Đùi gà góc tư chặt miếng nhỏ vừa ăn, ướp với sả băm, sa tế và nước mắm."},
            {"step": 2, "description": "Phi thơm hành tím, cho gà vào xào săn ở lửa lớn."},
            {"step": 3, "description": "Thêm chút nước lọc, kho lửa nhỏ đến khi nước cạn sệt và gà thấm đều gia vị."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 20, "total_time_minutes": 35
    },
    {
        "recipe_id": "R038",
        "name": "Canh rau ngót thịt bằm",
        "description": "Món canh quốc dân thanh mát, dễ nấu với thịt heo xay.",
        "category": "canh", "tags": ["thịt heo", "canh rau", "nhanh"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "thit_heo_xay", "required_qty_g": 50, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "cai_xanh", "required_qty_g": 65, "is_optional": False, "role": "vegetable"},
            {"ingredient_id": "hat_nem", "required_qty_g": 3, "is_optional": True, "role": "seasoning"}
        ],
        "steps": [
            {"step": 1, "description": "Rau cải xanh (dùng thay rau ngót nếu không có) rửa sạch, vò nhẹ hoặc thái nhỏ."},
            {"step": 2, "description": "Xào thịt heo xay với chút hành tím cho thơm, sau đó đổ nước vào đun sôi."},
            {"step": 3, "description": "Cho rau vào nấu chín tới, nêm hạt nêm vừa ăn rồi tắt bếp ngay để rau giữ màu xanh."}
        ],
        "prep_time_minutes": 10, "cook_time_minutes": 5, "total_time_minutes": 15
    },
    {
        "recipe_id": "R039",
        "name": "Bò bít tết đơn giản",
        "description": "Thịt thăn bò mềm mại áp chảo cùng tỏi, ăn kèm hành tây.",
        "category": "mon_chinh", "tags": ["thịt bò", "áp chảo", "sang trọng"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "thit_bo", "required_qty_g": 150, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "toi", "required_qty_g": 10, "is_optional": True, "role": "aromatic"},
            {"ingredient_id": "hanh_tay", "required_qty_g": 25, "is_optional": True, "role": "side_veg"},
            {"ingredient_id": "dau_an", "required_qty_g": 10, "is_optional": True, "role": "cooking_fat"}
        ],
        "steps": [
            {"step": 1, "description": "Thịt bò thăn thái miếng dày, dùng búa dần sơ cho mềm, ướp muối và tiêu đen."},
            {"step": 2, "description": "Đun nóng chảo với dầu ăn, cho tỏi nguyên tép vào phi thơm rồi áp chảo thịt bò."},
            {"step": 3, "description": "Áp chảo mỗi mặt khoảng 2-3 phút tùy độ chín mong muốn, ăn kèm hành tây xào sơ."}
        ],
        "prep_time_minutes": 10, "cook_time_minutes": 10, "total_time_minutes": 20
    },
    {
        "recipe_id": "R040",
        "name": "Canh bí đỏ thịt bằm",
        "description": "Bí đỏ bùi ngọt nấu cùng thịt heo xay, cung cấp nhiều vitamin A.",
        "category": "canh", "tags": ["bí đỏ", "thịt heo", "bổ dưỡng"], "servings": 1,
        "ingredients": [
            {"ingredient_id": "bi_do", "required_qty_g": 135, "is_optional": False, "role": "main_vegetable"},
            {"ingredient_id": "thit_heo_xay", "required_qty_g": 50, "is_optional": False, "role": "main_protein"},
            {"ingredient_id": "hanh_la", "required_qty_g": 3, "is_optional": True, "role": "garnish"}
        ],
        "steps": [
            {"step": 1, "description": "Bí đỏ gọt vỏ, thái miếng vuông vừa ăn. Thịt heo xay ướp chút gia vị."},
            {"step": 2, "description": "Đun sôi nước, cho thịt xay vào nấu lấy nước ngọt, vớt bọt."},
            {"step": 3, "description": "Cho bí đỏ vào hầm đến khi chín mềm, nêm nếm lại và rắc hành lá."}
        ],
        "prep_time_minutes": 15, "cook_time_minutes": 15, "total_time_minutes": 30
    }
]
