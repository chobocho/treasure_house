// 슬라이드 p11-v10-st-noctor — 초기화자만 있고 생성자가 없으면, C# 10.0
using System;

struct S
{
    public int X = 1;
    public int Y;
}

class App
{
    static void Main() => Console.WriteLine(new S().X);
}
