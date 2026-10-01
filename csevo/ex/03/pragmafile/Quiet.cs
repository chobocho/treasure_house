// 슬라이드 p3-v2-pragma-file — 끄고 restore 하지 않은 파일, C# 2.0
#pragma warning disable 168

partial class App
{
    static void Quiet()
    {
        int x;                           // off to the end of file
    }
}
