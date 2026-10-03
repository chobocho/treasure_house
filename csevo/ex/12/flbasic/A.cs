// 슬라이드 p12-v11-file — file 형식(A.cs), C# 11
file class Widget                // visible only in A.cs
{
    public static string Who => "Widget of A.cs";
}

static class A
{
    public static string Run() => Widget.Who;
}
