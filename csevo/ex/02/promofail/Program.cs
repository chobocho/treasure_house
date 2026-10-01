// 슬라이드 p2-v1-promofail — 좁은 정수끼리의 연산 결과는 int, C# 1.0
using System;

class App
{
    static void Main()
    {
        byte a = 200, b = 100;
        byte c = a + b;
        short s = 3;
        short t = s * s;
        char ch = 'a';
        char next = ch + 1;
        Console.WriteLine(c + t + next);
    }
}
