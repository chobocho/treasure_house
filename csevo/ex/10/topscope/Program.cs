// 슬라이드 p10-v9-top-scope — 최상위의 지역은 어디서나 보인다, C# 9.0
using System;

Console.WriteLine(Report.Make());
#if BAD
string Title = "local";        // same name as the class below
Console.WriteLine(Title);
#endif

static class Title
{
    public static string Text => "Report";
}

static class Report
{
    public static string Make() => Title.Text + " ok";
}
