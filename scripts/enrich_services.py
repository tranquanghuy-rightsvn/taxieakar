#!/usr/bin/env python3
"""Làm dày nội dung 4 trang dịch vụ (chạy 1 lần, idempotent nhờ marker svc-extra).

Chèn: đoạn giới thiệu thêm, khu vực phục vụ tại Ea Kar, nhu cầu thường gặp, FAQ (+ FAQPage
JSON-LD); đổi title/description/H1 tập trung từ khoá local "taxi Ea Kar".
"""
import html as H
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent / "html"
CHECK = ('<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" '
         'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M20 6L9 17l-5-5" /></svg>')
PIN = ('<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true">'
       '<path d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 '
       '12 6.5a2.5 2.5 0 0 1 0 5z" /></svg>')
CHEVRON = ('<svg class="svc-faq-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" '
           'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" '
           'aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>')

EAKAR_AREAS = ["Trung tâm Ea Kar", "Ea Knốp", "Ea Kmút", "Cư Huê", "Ea Đar", "Cư Ni", "Ea Păl",
               "Cư Prông", "Ea Ô", "Cư Yang", "Ea Sar", "Xuân Phú", "Cư Bông", "Ea Tíh",
               "Cư Elang", "Ea Sô"]
NEIGHBORS = ["Buôn Ma Thuột", "Krông Pắc", "M'Drắk", "Krông Bông", "Krông Năng"]

PAGES = {
    "di-noi-thanh": {
        "title": "Taxi Ea Kar Nội Thành 24/7, Đón Tận Nơi - Xe Taxi Eakar",
        "desc": "Taxi Ea Kar nội thành 24/7: xe 4 chỗ đời mới đón tận nơi ở Ea Knốp, Ea Kmút, "
                "Cư Huê và khắp Ea Kar, giá cước theo km báo trước. Gọi 0856 713 714.",
        "h1": "TAXI EA KAR ĐI NỘI THÀNH",
        "old_p2": "<p>Tài xế thông thạo địa bàn, đón trả tận nơi theo yêu cầu, phù hợp cho đi lại cá nhân, gia đình hoặc nhóm nhỏ.</p>",
        "intro": [
            "Khi cần gọi taxi Ea Kar, bạn chỉ cần một cuộc gọi tới hotline <strong>0856 713 714</strong>. "
            "Tổng đài nhận cuốc cả ngày lẫn đêm và điều xe gần nhất tới đón tại nhà, chợ, trường học, "
            "trạm y tế hay bến xe trong khu vực Ea Kar, Ea Knốp, Ea Kmút và các xã lân cận.",
            "Tài xế là người địa phương, thông thạo từng tuyến đường trong huyện nên đón đúng chỗ, đi "
            "đúng đường. Giá cước tính theo km và được báo trước khi xe chạy, phù hợp cho đi lại cá "
            "nhân, gia đình hoặc nhóm nhỏ.",
        ],
        "areas_title": "KHU VỰC ĐÓN KHÁCH TẠI EA KAR",
        "areas_text": "Xe Taxi Eakar đón trả khách khắp địa bàn Ea Kar, từ khu trung tâm tới các xã "
                      "xa. Khu vực xa trung tâm, bạn nên gọi trước ít phút để tổng đài điều xe kịp thời.",
        "areas": EAKAR_AREAS,
        "uses_title": "TAXI EA KAR PHỤC VỤ NHỮNG CHUYẾN NÀO?",
        "uses": [
            ("Đi chợ, mua sắm", "Đi chợ, siêu thị và cửa hàng trong trung tâm Ea Kar, có thể hẹn giờ để xe quay lại đón về."),
            ("Đi khám bệnh", "Đưa người lớn tuổi, người bệnh tới trạm y tế, bệnh viện trong huyện. Tài xế hỗ trợ lên xuống xe nhẹ nhàng."),
            ("Đưa đón người thân", "Đón người thân ở bến xe, dọc Quốc lộ 26 về tận nhà, đưa con em đi học hay đi thi."),
            ("Đi làm, đi việc", "Đi làm, đi ngân hàng, làm giấy tờ hay gặp khách trong ngày mà không phải lo chỗ gửi xe."),
            ("Về khuya, trời mưa", "Tổng đài 24/7, có xe cả lúc đêm muộn hay trời mưa, an toàn hơn tự chạy xe máy trên đường tối."),
            ("Đi tiệc, đám cưới", "Đi ăn tiệc, đám cưới, liên hoan có uống rượu bia thì gọi taxi về nhà, an toàn cho mình và mọi người."),
        ],
        "faq": [
            ("Gọi taxi Ea Kar ở đâu nhanh nhất?",
             "Gọi hotline 0856 713 714 (24/7) hoặc nhắn Zalo 0368 395 396. Bạn cũng có thể đặt nhanh ngay trên website bằng cách nhập điểm đón, điểm đến và thời gian."),
            ("Giá taxi nội thành Ea Kar bao nhiêu?",
             "Xe 4 chỗ: quãng dưới 10km giá 14k/km, dưới 100km giá 10k/km, từ 100km trở lên giá 9k/km. Đi khứ hồi lượt về giảm đến 70% tùy quãng đường. Tổng đài báo giá trước khi xe chạy."),
            ("Taxi có đón ở các xã xa trung tâm không?",
             "Có. Xe đón khách ở Ea Knốp, Ea Kmút, Cư Huê, Ea Ô, Cư Yang và các xã khác trong Ea Kar. Với khu vực xa, bạn nên gọi trước ít phút để tổng đài sắp xếp xe."),
            ("Có đặt taxi trước theo giờ được không?",
             "Được. Bạn đặt qua hotline hoặc ô đặt xe trên website, chọn ngày giờ cần đi, tài xế sẽ có mặt đúng hẹn. Rất tiện cho các chuyến đi sớm hoặc đi khám bệnh."),
            ("Taxi Eakar có chạy ban đêm không?",
             "Có. Tổng đài hoạt động 24/7, kể cả ban đêm, cuối tuần và ngày lễ."),
        ],
    },
    "di-cac-tinh": {
        "title": "Taxi Ea Kar Đi Buôn Ma Thuột, Liên Tỉnh - Xe Taxi Eakar",
        "desc": "Taxi Ea Kar đi Buôn Ma Thuột, các huyện Đắk Lắk và tỉnh lân cận: xe 4 chỗ đón tận "
                "nhà, chặng từ 100km chỉ 9k/km, khứ hồi giảm đến 70%. Gọi 0856 713 714.",
        "h1": "TAXI EA KAR ĐI CÁC TỈNH",
        "old_p2": "<p>Tài xế thông thạo địa bàn, đón trả tận nơi theo yêu cầu, phù hợp cho đi lại cá nhân, gia đình hoặc nhóm nhỏ.</p>",
        "intro": [
            "Taxi Ea Kar đi Buôn Ma Thuột (khoảng 52km) là tuyến được đặt nhiều nhất: đi khám bệnh "
            "ở bệnh viện tuyến tỉnh, làm thủ tục, ra bến xe hay thăm người thân. Ngoài ra xe nhận chạy "
            "các huyện trong tỉnh như Krông Pắc, M'Drắk, Krông Bông, Krông Năng và các tỉnh lân cận "
            "theo yêu cầu.",
            "Chặng càng dài giá càng tốt: từ 100km trở lên chỉ 9k/km, đi khứ hồi lượt về giảm đến 70% "
            "tùy quãng đường. Xe đón tận nhà và chạy theo giờ của bạn, không phải ra đường lớn chờ xe khách.",
        ],
        "areas_title": "ĐÓN KHÁCH ĐI TỈNH TỪ KHẮP EA KAR",
        "areas_text": "Bạn ở trung tâm hay các xã của Ea Kar đều được đón tận nhà, sau đó đi thẳng tới "
                      "nơi cần đến. Một số điểm đến thường gặp trong tỉnh:",
        "areas": EAKAR_AREAS[:8] + NEIGHBORS,
        "uses_title": "CÁC TUYẾN TAXI LIÊN TỈNH TỪ EA KAR",
        "uses": [
            ("Ea Kar đi Buôn Ma Thuột", "Khoảng 52km theo Quốc lộ 26. Đi khám bệnh, làm giấy tờ, mua sắm, có thể đi và về trong ngày."),
            ("Ea Kar đi sân bay", "Đưa đón sân bay Buôn Ma Thuột tận nhà, theo dõi giờ bay. Xem chi tiết ở trang <a href=\"/dua-don-san-bay/\">đưa đón sân bay</a>."),
            ("Ea Kar đi các huyện", "Krông Pắc, M'Drắk, Krông Bông, Krông Năng và các huyện khác trong Đắk Lắk, đón trả tận nơi."),
            ("Ea Kar đi tỉnh lân cận", "Tuyến Quốc lộ 26 về hướng Khánh Hòa và các tỉnh lân cận, báo giá theo km trước khi khởi hành."),
            ("Về quê dịp lễ Tết", "Đón người thân từ bến xe về Ea Kar hoặc đưa cả nhà về quê. Dịp lễ Tết nên đặt xe sớm."),
            ("Đi khứ hồi trong ngày", "Lượt về giảm đến 70% tùy quãng đường, tiết kiệm hơn gọi hai chuyến lẻ."),
        ],
        "faq": [
            ("Taxi Ea Kar đi Buôn Ma Thuột giá bao nhiêu?",
             "Quãng đường khoảng 52km, tính theo bảng giá xe 4 chỗ theo km. Giá trọn chuyến tùy điểm đón và điểm trả cụ thể, tổng đài báo trước khi xe chạy để bạn yên tâm."),
            ("Đi khứ hồi có rẻ hơn không?",
             "Có. Đi khứ hồi thì lượt về được giảm đến 70% tùy quãng đường."),
            ("Phí cầu đường ai thanh toán?",
             "Phí đường bộ (nếu có) do khách thanh toán, ngoài giá cước theo km."),
            ("Có cần đặt xe đi tỉnh trước không?",
             "Với chặng dài, chuyến đi sớm hoặc dịp lễ Tết, bạn nên đặt trước để tổng đài xếp xe. Chuyến gấp vẫn có thể gọi hotline 0856 713 714 bất cứ lúc nào."),
            ("Xe có nhận đi tỉnh xa không?",
             "Có, theo yêu cầu của khách. Chặng từ 100km trở lên áp dụng giá 9k/km, gọi hotline để được báo giá cụ thể."),
        ],
    },
    "dua-don-san-bay": {
        "title": "Taxi Ea Kar Đưa Đón Sân Bay Buôn Ma Thuột - Xe Taxi Eakar",
        "desc": "Taxi Ea Kar đưa đón sân bay Buôn Ma Thuột: xe 7 chỗ rộng rãi, theo dõi giờ bay, "
                "đón trả tận nhà ở Ea Kar, Ea Knốp, Ea Kmút, hỗ trợ hành lý. Gọi 0856 713 714.",
        "h1": "TAXI EA KAR ĐƯA ĐÓN SÂN BAY",
        "old_p2": "<p>Tài xế theo dõi giờ bay, sắp xếp đón trả đúng thời gian, hỗ trợ hành lý tận tình trong suốt hành trình.</p>",
        "intro": [
            "Tài xế theo dõi giờ bay, sắp xếp đón trả đúng thời gian, hỗ trợ hành lý tận tình trong suốt hành trình.",
            "Chiều đi, xe đón tận nhà ở trung tâm Ea Kar, Ea Knốp, Ea Kmút hay các xã lân cận và đưa "
            "thẳng tới sân bay Buôn Ma Thuột. Chiều về, tài xế đón bạn tại sân bay và chở về tận cửa nhà, "
            "không phải tìm xe hay hỏi giá khi vừa xuống máy bay.",
        ],
        "areas_title": "ĐÓN TRẢ SÂN BAY TẬN NHÀ TẠI EA KAR",
        "areas_text": "Taxi Ea Kar đưa đón sân bay cho khách ở khắp địa bàn Ea Kar. Chuyến bay sớm, "
                      "bạn nên đặt xe từ hôm trước để tài xế chủ động giờ đón.",
        "areas": EAKAR_AREAS,
        "uses_title": "AI NÊN ĐẶT XE ĐƯA ĐÓN SÂN BAY?",
        "uses": [
            ("Gia đình có trẻ nhỏ", "Xe 7 chỗ rộng, cả nhà ngồi thoải mái, người lớn tuổi và trẻ nhỏ không phải chen chúc xe khách."),
            ("Khách nhiều hành lý", "Cốp xe rộng, tài xế hỗ trợ mang vác hành lý lên xuống xe."),
            ("Bay sớm hoặc đêm muộn", "Tổng đài 24/7, có xe cả những chuyến bay sáng sớm hay hạ cánh lúc khuya."),
            ("Đón người thân về Ea Kar", "Báo số hiệu chuyến bay, tài xế đón đúng giờ hạ cánh rồi đưa người thân về tận nhà."),
            ("Đi công tác", "Đúng giờ, chủ động lịch trình, có thể đặt chiều đi và chiều về cùng lúc."),
            ("Đoàn khách nhỏ", "Một xe 7 chỗ chở được cả nhóm, tiện hơn gọi nhiều xe riêng lẻ."),
        ],
        "faq": [
            ("Nên đặt xe ra sân bay trước bao lâu?",
             "Bạn nên đặt ngay khi có vé, muộn nhất vài giờ trước giờ đón. Tổng đài sẽ tính giờ xuất phát để bạn tới sân bay sớm, đủ thời gian làm thủ tục."),
            ("Máy bay trễ chuyến thì sao?",
             "Tài xế theo dõi giờ bay và đón theo giờ hạ cánh thực tế. Bạn chỉ cần báo số hiệu chuyến bay khi đặt xe."),
            ("Giá taxi Ea Kar đi sân bay bao nhiêu?",
             "Xe 7 chỗ: quãng dưới 10km giá 18k/km, dưới 100km giá 15k/km, từ 100km trở lên giá 11k/km. Tổng đài báo giá trọn chuyến trước khi đi."),
            ("Khi đặt xe cần cung cấp thông tin gì?",
             "Họ tên, số điện thoại, địa chỉ đón hoặc trả, số hiệu chuyến bay và giờ bay."),
            ("Có đón sân bay vào ban đêm không?",
             "Có. Tổng đài hoạt động 24/7 nên chuyến bay hạ cánh muộn vẫn có xe đón về Ea Kar."),
        ],
    },
    "hop-dong-du-lich-tron-goi": {
        "title": "Thuê Xe Hợp Đồng Du Lịch Ea Kar Trọn Gói - Xe Taxi Eakar",
        "desc": "Thuê xe hợp đồng du lịch trọn gói từ Ea Kar: xe 4 - 7 chỗ đi Buôn Ma Thuột, Hồ Lắk, "
                "Buôn Đôn, Dray Nur, đi công tác, sự kiện. Báo giá theo lộ trình. Gọi 0856 713 714.",
        "h1": "XE HỢP ĐỒNG DU LỊCH EA KAR",
        "old_p2": "<p>Lịch trình được sắp xếp linh hoạt theo yêu cầu, tài xế am hiểu địa bàn và các điểm du lịch nổi tiếng trong khu vực.</p>",
        "intro": [
            "Lịch trình được sắp xếp linh hoạt theo yêu cầu, tài xế am hiểu địa bàn và các điểm du lịch nổi tiếng trong khu vực.",
            "Từ Ea Kar, các điểm tham quan quen thuộc như Buôn Ma Thuột, thác Dray Nur, Hồ Lắk hay Buôn "
            "Đôn đều đi về được trong ngày. Bạn chỉ cần cho biết số người, nơi muốn tới và giờ xuất phát, "
            "tổng đài sẽ gợi ý loại xe phù hợp và báo giá trọn gói đã gồm xăng xe và tài xế.",
        ],
        "areas_title": "ĐÓN ĐOÀN TẬN NƠI TẠI EA KAR",
        "areas_text": "Xe hợp đồng đón khách tại nhà, cơ quan hoặc điểm tập trung ở khắp Ea Kar, rồi "
                      "đi theo lịch trình đã thống nhất. Điểm đón thường gặp:",
        "areas": EAKAR_AREAS,
        "uses_title": "THUÊ XE HỢP ĐỒNG EA KAR CHO NHỮNG DỊP NÀO?",
        "uses": [
            ("Du lịch trong ngày", "Buôn Ma Thuột, thác Dray Nur, Hồ Lắk, Buôn Đôn: đi sáng về chiều, dừng nghỉ theo ý đoàn."),
            ("Đi công tác", "Đi họp, gặp đối tác, làm việc nhiều điểm trong ngày, xe chờ và chở tiếp theo lịch."),
            ("Đám cưới, việc hiếu hỉ", "Đưa đón họ hàng, khách mời đi về đúng giờ trong ngày vui của gia đình."),
            ("Sự kiện, đưa đón đoàn", "Đưa đón nhân viên, khách mời dự hội nghị, liên hoan, tất niên."),
            ("Về quê dịp lễ Tết", "Cả nhà đi chung một xe, chủ động giờ đi, chở được nhiều đồ đạc."),
            ("Thuê theo ngày", "Thuê xe theo ngày hoặc theo chuyến, báo giá rõ ràng theo lộ trình trước khi đi."),
        ],
        "faq": [
            ("Giá thuê xe trọn gói đã gồm những gì?",
             "Giá đã gồm xăng xe và tài xế. Giá chưa gồm vé tham quan và phí cầu đường."),
            ("Thuê xe 7 chỗ giá thế nào?",
             "Bảng giá tham khảo tính cho xe 4 chỗ, trọn gói khứ hồi trong ngày. Xe 7 chỗ cộng thêm 200k - 300k tùy lộ trình."),
            ("Có đi nhiều điểm trong một ngày được không?",
             "Được. Lịch trình linh hoạt theo yêu cầu, bạn báo trước các điểm muốn ghé để tổng đài báo giá theo lộ trình."),
            ("Nên đặt xe hợp đồng trước bao lâu?",
             "Chuyến cuối tuần, dịp lễ Tết hoặc mùa cưới nên đặt sớm vài ngày để chắc chắn có xe đúng loại."),
            ("Có thuê xe nhiều ngày không?",
             "Có. Xe nhận hợp đồng theo ngày hoặc theo chuyến, gọi hotline 0856 713 714 để được tư vấn lịch trình và báo giá."),
        ],
    },
}


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def sections(cfg):
    chips = "\n".join('          <li class="svc-area">%s%s</li>' % (PIN, H.escape(a)) for a in cfg["areas"])
    uses = "\n".join(
        '          <li class="svc-use"><span class="svc-use-icon">%s</span><div><h3>%s</h3><p>%s</p></div></li>'
        % (CHECK, H.escape(t), d) for t, d in cfg["uses"])
    faq = "\n".join(
        '          <details class="svc-faq-item"><summary>%s%s</summary><p>%s</p></details>'
        % (H.escape(q), CHEVRON, H.escape(a)) for q, a in cfg["faq"])
    areas_html = """    <!-- svc-extra:areas -->
    <section class="svc-areas">
      <div class="about-inner">
        <div class="section-heading why-us-heading">
          <h2 class="section-title">%s</h2>
          <span class="section-title-bar"></span>
        </div>
        <p class="svc-lead">%s</p>
        <ul class="svc-area-list">
%s
        </ul>
      </div>
    </section>

""" % (cfg["areas_title"], H.escape(cfg["areas_text"]), chips)
    uses_faq_html = """    <!-- svc-extra:uses -->
    <section class="svc-uses">
      <div class="about-inner">
        <div class="section-heading why-us-heading">
          <h2 class="section-title">%s</h2>
          <span class="section-title-bar"></span>
        </div>
        <ul class="svc-use-list">
%s
        </ul>
      </div>
    </section>

    <section class="svc-faq">
      <div class="svc-faq-inner">
        <div class="section-heading why-us-heading">
          <h2 class="section-title">CÂU HỎI THƯỜNG GẶP</h2>
          <span class="section-title-bar"></span>
        </div>
        <div class="svc-faq-list">
%s
        </div>
      </div>
    </section>

""" % (cfg["uses_title"], uses, faq)
    return areas_html, uses_faq_html


def faq_ld(slug, cfg):
    node = {
        "@type": "FAQPage",
        "@id": "https://taxieakar.com.vn/%s/#faq" % slug,
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in cfg["faq"]],
    }
    return json.dumps(node, ensure_ascii=False, indent=2)


def one(s, old, new, what):
    assert s.count(old) == 1, "%s: tìm thấy %d lần" % (what, s.count(old))
    return s.replace(old, new)


def main():
    for slug, cfg in PAGES.items():
        f = ROOT / slug / "index.html"
        s = f.read_text(encoding="utf-8")
        if "svc-extra:areas" in s:
            print("bỏ qua (đã có)", slug)
            continue
        old_title = re.search(r"<title>([^<]*)</title>", s).group(1)
        old_desc = re.search(r'<meta name="description" content="([^"]*)"', s).group(1)
        s = s.replace(old_title, cfg["title"])
        s = s.replace(old_desc, cfg["desc"])
        s = re.sub(r"<h1>[^<]*</h1>", "<h1>%s</h1>" % cfg["h1"], s, count=1)

        intro = "\n\n".join("            <p>%s</p>" % p for p in cfg["intro"])
        s = one(s, "            " + cfg["old_p2"], intro, slug + " intro")

        areas_html, uses_faq_html = sections(cfg)
        s = one(s, '    <section class="process-section">', areas_html + '    <section class="process-section">', slug + " process")
        s = one(s, '    <section class="commitment">', uses_faq_html + '    <section class="commitment">', slug + " commitment")

        # FAQPage vào cuối @graph (sau node TaxiService là node cuối).
        m = list(re.finditer(r"\n      \}\n    \]\n  \}\n  </script>", s))
        assert len(m) == 1, slug + " ld+json end"
        node = "\n".join("      " + ln for ln in faq_ld(slug, cfg).splitlines())
        s = s[:m[0].start()] + "\n      },\n" + node + "\n    ]\n  }\n  </script>" + s[m[0].end():]
        ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S).group(1)
        json.loads(ld)
        f.write_text(s, encoding="utf-8")
        print("OK", slug, len(strip_tags(areas_html + uses_faq_html + intro).split()), "chữ thêm")


if __name__ == "__main__":
    main()
