// 슬라이드 p5-v4-named-rename — 매개변수 이름이 API 가 된다, C# 4.0
using System;

static class Library
{
    // version 2 renamed 'width' to 'w'
    public static string Resize(int w, int height)
    {
        return w + "x" + height;
    }
}

class Program
{
    static void Main()
    {
        Console.WriteLine(Library.Resize(640, 480));
        Console.WriteLine(Library.Resize(width: 640, height: 480));
    }
}
