// 슬라이드 p8-v7-locfn-shadow8 — 지역 함수가 바깥 이름을 가리기, C# 8.0
using System;

class App
{
    static void Main()
    {
        int x = 10;
        Console.WriteLine(Twice(3) + " " + x);

        int Twice(int x) => x * 2;      // parameter x hides local x
    }
}
