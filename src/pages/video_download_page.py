"""
Video Download Interface
واجهة تحميل الفيديوهات

Professional interface for downloading videos from 1000+ websites
"""

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from src.utils.video_downloader import VideoDownloader, YT_DLP_AVAILABLE
except ImportError:
    VideoDownloader = None
    YT_DLP_AVAILABLE = False


def show_video_download_page():
    """Main video download interface"""

    st.title("🎬 Video Downloader - تحميل الفيديوهات")

    # Check if yt-dlp is available
    if not YT_DLP_AVAILABLE:
        st.error("""
        ### ❌ yt-dlp غير مثبت

        هذه الميزة تحتاج yt-dlp لتحميل الفيديوهات.
        """)

        st.subheader("📦 التثبيت:")
        st.code("pip install yt-dlp", language="bash")

        st.info("""
        **yt-dlp** هي أداة قوية تدعم أكثر من 1000 موقع:
        - ✅ YouTube, Vimeo, Dailymotion
        - ✅ Facebook, Instagram, Twitter, TikTok
        - ✅ Twitch, Reddit, Streamable
        - ✅ ESPN, NHL, NBA (مواقع رياضية)
        - ✅ وأكثر من 1000 موقع آخر!
        """)
        return

    # Initialize downloader
    if 'downloader' not in st.session_state:
        st.session_state.downloader = VideoDownloader(
            output_dir='data/training_videos',
            quality='best',
            organize_by_source=True
        )

    downloader = st.session_state.downloader

    # Sidebar - Settings
    with st.sidebar:
        st.subheader("⚙️ الإعدادات")

        output_dir = st.text_input(
            "📁 مجلد الحفظ",
            value="data/training_videos",
            help="المجلد الذي سيتم حفظ الفيديوهات فيه"
        )

        quality = st.selectbox(
            "🎥 الجودة",
            ['best', '1080p', '720p', '480p', '360p', 'worst'],
            index=0,
            help="اختر جودة الفيديو"
        )

        organize = st.checkbox(
            "📂 ترتيب حسب الموقع",
            value=True,
            help="إنشاء مجلد منفصل لكل موقع"
        )

        if st.button("💾 حفظ الإعدادات"):
            st.session_state.downloader = VideoDownloader(
                output_dir=output_dir,
                quality=quality,
                organize_by_source=organize
            )
            st.success("✅ تم حفظ الإعدادات")

        st.markdown("---")

        # Statistics
        st.subheader("📊 الإحصائيات")
        stats = downloader.get_stats()
        st.metric("إجمالي التحميلات", stats['total_downloads'])
        st.metric("نجح", stats['successful'])
        st.metric("فشل", stats['failed'])
        st.metric("الحجم (MB)", f"{stats['total_size_mb']:.2f}")

        st.markdown("---")

        # Supported sites
        with st.expander("🌐 المواقع المدعومة (عينة)"):
            sites = downloader.supported_sites()
            for site in sites[:15]:
                st.text(f"✅ {site}")
            st.text(f"... وأكثر من 1000 موقع!")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎥 فيديو واحد",
        "📋 قائمة تشغيل",
        "📝 تحميل متعدد",
        "🔍 بحث وتحميل"
    ])

    # Tab 1: Single Video Download
    with tab1:
        st.subheader("تحميل فيديو واحد")

        url = st.text_input(
            "🔗 رابط الفيديو",
            placeholder="https://www.youtube.com/watch?v=...",
            help="الصق رابط الفيديو من أي موقع مدعوم"
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            custom_name = st.text_input(
                "📝 اسم مخصص (اختياري)",
                placeholder="اترك فارغاً لاستخدام العنوان الأصلي",
                help="اسم الملف بدون امتداد"
            )

        with col2:
            check_info = st.button("ℹ️ معلومات الفيديو", use_container_width=True)

        # Check video info
        if check_info and url:
            with st.spinner("جاري جلب المعلومات..."):
                info = downloader.get_video_info(url)

                if info:
                    st.success("✅ الفيديو متوفر!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.image(info.thumbnail, use_column_width=True)
                    with col2:
                        st.write(f"**العنوان:** {info.title}")
                        st.write(f"**المدة:** {info.duration // 60}:{info.duration % 60:02d}")
                        st.write(f"**الناشر:** {info.uploader}")
                    with col3:
                        if info.view_count:
                            st.metric("المشاهدات", f"{info.view_count:,}")
                        if info.like_count:
                            st.metric("الإعجابات", f"{info.like_count:,}")
                else:
                    st.error("❌ فشل في جلب معلومات الفيديو. تحقق من الرابط.")

        # Download button
        if st.button("⬇️ تحميل الفيديو", type="primary", use_container_width=True):
            if not url:
                st.error("⚠️ الرجاء إدخال رابط الفيديو")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()

                def progress_callback(progress):
                    percent_str = progress.get('percent', '0%')
                    # Extract number from percent string
                    try:
                        percent_num = float(percent_str.replace('%', ''))
                        progress_bar.progress(min(percent_num / 100, 1.0))
                    except:
                        pass

                    status_text.text(
                        f"⬇️ التحميل: {percent_str} | "
                        f"السرعة: {progress.get('speed', 'N/A')} | "
                        f"الوقت المتبقي: {progress.get('eta', 'N/A')}"
                    )

                with st.spinner("جاري التحميل..."):
                    result = downloader.download_video(
                        url,
                        output_filename=custom_name if custom_name else None,
                        progress_callback=progress_callback
                    )

                if result.success:
                    st.success(f"✅ تم التحميل بنجاح: {result.title}")
                    st.info(f"📁 الملف محفوظ في: `{result.filepath}`")

                    # Show download time
                    if result.duration:
                        st.write(f"⏱️ وقت التحميل: {result.duration:.2f} ثانية")
                else:
                    st.error(f"❌ فشل التحميل: {result.error}")

    # Tab 2: Playlist Download
    with tab2:
        st.subheader("تحميل قائمة تشغيل كاملة")

        playlist_url = st.text_input(
            "🔗 رابط قائمة التشغيل",
            placeholder="https://www.youtube.com/playlist?list=...",
            help="الصق رابط قائمة التشغيل"
        )

        col1, col2 = st.columns(2)

        with col1:
            max_videos = st.number_input(
                "📊 أقصى عدد من الفيديوهات",
                min_value=1,
                max_value=1000,
                value=10,
                help="حدد كم فيديو تريد تحميله (اترك 1000 لتحميل الكل)"
            )

        with col2:
            check_playlist = st.button("ℹ️ معلومات القائمة", use_container_width=True)

        # Check playlist info
        if check_playlist and playlist_url:
            with st.spinner("جاري جلب معلومات القائمة..."):
                info = downloader.get_playlist_info(playlist_url)

                if info:
                    if info['is_playlist']:
                        st.success(f"✅ قائمة تشغيل: {info['title']}")
                        st.write(f"**عدد الفيديوهات:** {info['video_count']}")
                        st.write(f"**الناشر:** {info.get('uploader', 'Unknown')}")

                        # Show first few videos
                        if 'videos' in info and info['videos']:
                            st.write("**أول 5 فيديوهات:**")
                            for video in info['videos'][:5]:
                                st.text(f"• {video['title']}")
                    else:
                        st.warning("⚠️ هذا رابط فيديو واحد وليس قائمة تشغيل")
                else:
                    st.error("❌ فشل في جلب معلومات القائمة")

        # Download playlist button
        if st.button("⬇️ تحميل القائمة", type="primary", use_container_width=True):
            if not playlist_url:
                st.error("⚠️ الرجاء إدخال رابط قائمة التشغيل")
            else:
                progress_container = st.container()

                with progress_container:
                    st.write("**جاري تحميل القائمة...**")
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    results = []
                    total = max_videos

                    def progress_callback(progress):
                        if 'playlist_progress' in progress:
                            current, total_vids = progress['playlist_progress'].split('/')
                            progress_bar.progress(int(current) / int(total_vids))
                            status_text.text(
                                f"📥 الفيديو {progress['playlist_progress']} | "
                                f"{progress.get('percent', '0%')}"
                            )

                    results = downloader.download_playlist(
                        playlist_url,
                        max_videos=max_videos if max_videos < 1000 else None,
                        progress_callback=progress_callback
                    )

                    # Summary
                    st.markdown("---")
                    st.subheader("📊 ملخص التحميل")

                    successful = sum(1 for r in results if r.success)
                    failed = sum(1 for r in results if not r.success)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("الإجمالي", len(results))
                    with col2:
                        st.metric("نجح", successful, delta=f"+{successful}")
                    with col3:
                        st.metric("فشل", failed, delta=f"-{failed}" if failed > 0 else "0")

                    # Show failed downloads if any
                    if failed > 0:
                        with st.expander("❌ الفيديوهات الفاشلة"):
                            for result in results:
                                if not result.success:
                                    st.text(f"• {result.title}: {result.error}")

    # Tab 3: Batch Download
    with tab3:
        st.subheader("تحميل متعدد من روابط مختلفة")

        st.write("**الصق عدة روابط (كل رابط في سطر جديد):**")

        urls_text = st.text_area(
            "🔗 الروابط",
            height=200,
            placeholder="https://www.youtube.com/watch?v=...\nhttps://vimeo.com/...\nhttps://www.instagram.com/...",
            help="الصق كل رابط في سطر منفصل"
        )

        # Parse URLs
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]

        if urls:
            st.info(f"📊 عدد الروابط: {len(urls)}")

        # Download all button
        if st.button("⬇️ تحميل الكل", type="primary", use_container_width=True):
            if not urls:
                st.error("⚠️ الرجاء إدخال روابط للتحميل")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()

                def progress_callback(progress):
                    if 'batch_progress' in progress:
                        current, total_vids = progress['batch_progress'].split('/')
                        progress_bar.progress(int(current) / int(total_vids))
                        status_text.text(
                            f"📥 الفيديو {progress['batch_progress']} | "
                            f"{progress.get('percent', '0%')}"
                        )

                results = downloader.download_batch(urls, progress_callback=progress_callback)

                # Summary
                st.markdown("---")
                st.subheader("📊 ملخص التحميل")

                successful = sum(1 for r in results if r.success)
                failed = sum(1 for r in results if not r.success)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("الإجمالي", len(results))
                with col2:
                    st.metric("نجح", successful)
                with col3:
                    st.metric("فشل", failed)

                # Details
                with st.expander("📋 التفاصيل الكاملة"):
                    for i, result in enumerate(results, 1):
                        if result.success:
                            st.success(f"{i}. ✅ {result.title}")
                        else:
                            st.error(f"{i}. ❌ {result.title}: {result.error}")

    # Tab 4: Search and Download
    with tab4:
        st.subheader("🔍 البحث والتحميل")

        st.info("""
        **ابحث عن فيديوهات على YouTube وقم بتحميلها مباشرة!**

        مثالي لبناء dataset للتدريب.
        """)

        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input(
                "🔍 كلمة البحث",
                placeholder="figure skating jumps",
                help="ابحث عن فيديوهات على YouTube"
            )

        with col2:
            max_results = st.number_input(
                "عدد النتائج",
                min_value=1,
                max_value=50,
                value=10
            )

        if st.button("🔍 بحث وتحميل", type="primary", use_container_width=True):
            if not search_query:
                st.error("⚠️ الرجاء إدخال كلمة البحث")
            else:
                with st.spinner(f"جاري البحث عن '{search_query}'..."):
                    results = downloader.search_and_download(
                        query=search_query,
                        max_results=max_results
                    )

                    if results:
                        st.success(f"✅ تم تحميل {len(results)} فيديو")

                        # Show results
                        for result in results:
                            if result.success:
                                st.write(f"✅ {result.title}")
                            else:
                                st.write(f"❌ {result.title}: {result.error}")
                    else:
                        st.warning("لم يتم العثور على نتائج")

    # Footer
    st.markdown("---")
    st.info("""
    💡 **نصائح:**
    - استخدم فيديوهات عالية الجودة للتدريب
    - نظّم الفيديوهات في مجلدات حسب نوع العنصر (jumps, spins, steps)
    - تأكد من وجود تنوع في المستويات (مبتدئين، متوسطين، محترفين)
    - احفظ معلومات الفيديو (JSON) لاستخدامها في التعليق
    """)


if __name__ == "__main__":
    show_video_download_page()
