// 슬라이드 p2-v1-overamb — 모호한 호출은 컴파일 오류, C# 1.0
using System;
using System.Collections;

class App
{
    static void G(string s) { Console.WriteLine("string"); }
    static void G(ArrayList a) { Console.WriteLine("ArrayList"); }

    static void H(int a, long b) { Console.WriteLine("int, long"); }
    static void H(long a, int b) { Console.WriteLine("long, int"); }

    static void Main()
    {
        G(null);                       // string or ArrayList?
        H(1, 1);                       // each wins one argument
        G((string)null);               // a cast settles it
        H(1, 1L);
    }
}
