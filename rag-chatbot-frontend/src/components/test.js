import React, { useState, useRef, useEffect } from "react";
import { uploadLandmarkInfo } from "../services/api";


function TestComponent() {
    const landmarkData = {
        "_id": "67f3edb13834bd66e6e1c672",
        "name": "Dinh Độc Lập",
        "description": "Dinh Độc Lập là một tòa nhà của nhà nước tại Thành phố Hồ Chí Minh,từng là nơi ở và làm việc của Tổng thống Việt Nam Cộng hòa trước Sự kiện 30 tháng 4 năm 1975.Hiện nay,Dinh Độc Lập đã được Chính phủ Việt Nam xếp hạng là di tích quốc gia đặc biệt.Cơ quan quản lý di tích văn hoá Dinh Độc Lập có tên là Hội trường Thống Nhất thuộc Văn phòng Chính phủ.",
        "images": [
            "https://ik.imagekit.io/tvlk/blog/2023/01/dinh-doc-lap-1.jpg?tr=dpr-2,w-675"
        ],
        "location": "Quận 1,Thành phố Hồ Chí Minh",
        "coordinates": {
            "latitude": "10°46′37″B",
            "longitude": "106°41′43″Đ"
        },
        "stats": {
            "averageRating": 0,
            "totalReviews": 0,
            "totalVisits": 0,
            "totalFavorites": 0
        },
        "knowledgeTestId": null,
        "leaderboardId": null,
        "leaderboardSummary": {
            "topScore": 0,
            "topUser": {
                "userId": null,
                "userName": ""
            },
            "totalParticipants": 0
        },
        "knowledgeTestSummary": {
            "title": "",
            "questionCount": 0,
            "difficulty": "Medium"
        },
        "rolePlayIds": [],
        "additionalInfo": {
            "architectural": null,
            "culturalFestival": null,
            "historicalEvents": [
                {
                    "title": "Thời Việt Nam Cộng hòa",
                    "description": "Dinh Độc Lập hiện nay được Tổng thống Ngô Đình Diệm cho khởi công xây dựng ngày 1 tháng 7 năm 1962,sau khi dinh cũ từ thời Pháp thuộc bị hư hại do vụ đánh bom của hai phi công.Dinh được xây theo bản thiết kế của kiến trúc sư Ngô Viết Thụ,người Việt Nam đầu tiên đạt giải Khôi nguyên La Mã.Trong thời gian xây dựng,gia đình Tổng thống Ngô Đình Diệm tạm thời chuyển sang sống tại Dinh Gia Long.Công trình đang xây dựng dở dang thì Ngô Đình Diệm bị phe đảo chính ám sát ngày 2 tháng 11 năm 1963.Do vậy,ngày khánh thành dinh,31 tháng 10 năm 1966,người chủ tọa buổi lễ là Nguyễn Văn Thiệu,Chủ tịch Ủy ban Lãnh đạo Quốc gia.Từ ngày này,Dinh Độc Lập mới xây dựng trở thành nơi ở và làm việc của tổng thống Việt Nam Cộng hòa.Tổng thống Nguyễn Văn Thiệu sống ở dinh này từ tháng 10 năm 1967 đến ngày 21 tháng 4 năm 1975.Ngày 8 tháng 4 năm 1975,chiếc máy bay F-5E do phi công Nguyễn Thành Trung lái,xuất phát từ Biên Hòa,đã ném bom Dinh nhằm mục đích ám sát Tổng thống Nguyễn Văn Thiệu,gây hư hại không đáng kể.Lúc 10 giờ 45 phút ngày 30 tháng 4 năm 1975,xe tăng T54B mang số hiệu 843 của Quân đội Nhân dân Việt Nam dưới quyền chỉ huy của Trung úy Bùi Quang Thận đã húc nghiêng cổng phụ của Dinh Độc Lập,tiếp đó xe tăng Type 59 mang số hiệu 390 do Vũ Đăng Toàn chỉ huy đã húc tung cổng chính tiến thẳng vào dinh.Lúc 11 giờ 30 phút cùng ngày,Trung úy Quân Giải phóng Bùi Quang Thận,đại đội trưởng,chỉ huy xe 843,đã hạ quốc kỳ Việt Nam Cộng hòa trên nóc dinh xuống,kéo lá cờ Mặt trận Dân tộc Giải phóng miền Nam Việt Nam lên,kết thúc 20 năm cuộc chiến tranh Việt Nam"
                },
                {
                    "title": "Sau năm 1975",
                    "description": "Sau hội nghị hiệp thương chính trị thống nhất hai miền Nam Bắc thành một đất nước Việt Nam thống nhất diễn ra tại dinh Độc Lập vào tháng 11 năm 1975.Cơ quan hiện quản lý di tích văn hoá Dinh Độc Lập có tên là Hội trường Thống Nhất thuộc Cục Hành chính Quản trị II - Văn phòng Chính phủ.Đây là di tích lịch sử văn hoá nổi tiếng được đông đảo du khách trong nước và nước ngoài đến tham quan.Nơi này được công nhận là Di tích lịch sử văn hóa quốc gia tại Quyết định số 77A/VHQĐ ngày 25/6/1976 của Bộ trưởng Bộ Văn hóa (Bộ Văn hóa,Thể thao và Du lịch ngày nay).Thủ tướng Chính phủ nước Cộng hòa Xã hội Chủ nghĩa Việt Nam đã ký Quyết định số 1272/QĐ-TTg xếp hạng Di tích lịch sử Dinh Độc Lập là một trong 10 di tích quốc gia đặc biệt đầu tiên của Việt Nam vào ngày 12 tháng 8 năm 2009.Ngày nay,Dinh Độc Lập trở thành một trong những địa điểm du lịch không thể thiếu của mỗi người dân khi tới Thành phố Hồ Chí Minh.Không chỉ có ý nghĩa về lịch sử mà Dinh Độc Lập còn thể hiện nét kiến trúc tiêu biểu của Việt Nam thời kì những thập niên 60.Ngoài ra,Dinh Độc Lập thường là nơi diễn ra các sự kiện lớn tổ chức tại thành phố,các buổi tiếp khách của Đảng,Nhà nước tại TPHCM cũng như chính quyền thành phố.Đồng thời là nơi tổ chức quốc tang cho các lãnh đạo Đảng,Nhà nước ở TPHCM và là điểm dừng cuối cùng của giải đua Cúp Truyền Hình HTV hàng năm."
                }
            ]
        },
        "status": "ACTIVE",
        "popularTags": [
            "Di tích lịch sử"
        ],
        "createdAt": "2025-04-07T15:22:24.935Z",
        "updatedAt": null,
        "locationSlug": "quan-1-thanh-pho-ho-chi-minh",
        "nameSlug": "dinh-doc-lap",
        "tagsSlug": [
            "di-tich-lich-su"
        ]
    };

    const handleUploadLandmark = async () => {
        try {
            const response = await uploadLandmarkInfo(landmarkData);
            console.log(`Upload successfully: ${response.message} with file_id: ${response.file_id}`);
            alert(`Success: ${response.message} (file id: ${response.file_id})`);
        }
        catch (error) {
            console.log(`Upload failed: ${error}`);
            alert(`Error uploading landmark: ${error.message}`);
        }
    };

    return (
      <div>
          <button onClick={handleUploadLandmark}>Upload Dinh Độc Lập Info</button>
      </div>
    )
};

export default TestComponent;