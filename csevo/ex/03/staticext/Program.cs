// 슬라이드 p3-v2-static-later — 확장 메서드는 static 클래스에만, C# 3.0
using System;

static class Good
{
    public static int Twice(this int x) { return x * 2; }
}

class Bad                            // not static
{
    public static int Thrice(this int x) { return x * 3; }
}

class App
{
    static void Main() { Console.WriteLine(4.Twice()); }
}
