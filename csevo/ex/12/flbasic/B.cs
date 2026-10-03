// 슬라이드 p12-v11-file — file 형식(B.cs), C# 11
file class Widget                // same name, another type
{
    public static string Who => "Widget of B.cs";
}

static class B
{
    public static string Run() => Widget.Who;
}
