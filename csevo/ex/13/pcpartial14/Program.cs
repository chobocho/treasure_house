// 슬라이드 p13-v12-pc-later — 기본 생성자와 partial 생성자, C# 14.0
using System;

partial class Temp(double celsius)
{
    public double C => celsius;
    public partial Temp(string text);           // defining declaration
}

partial class Temp
{
    public partial Temp(string text)            // implementing one
        : this(double.Parse(text.TrimEnd('C')))
    {
        Console.WriteLine("parsed " + text);
    }
}

class App
{
    static void Main() => Console.WriteLine(new Temp("21.5C").C);
}
