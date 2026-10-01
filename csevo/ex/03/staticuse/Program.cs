// 슬라이드 p3-v2-static-refused — static 클래스를 형식으로 쓰면, C# 2.0
using System;
using System.Collections.Generic;

static class Util { public static int One() { return 1; } }

class App
{
    static void Main()
    {
        object o = new Util();                     // instance
        Util u = null;                             // variable
        List<Util> list = null;                    // type argument
        Console.WriteLine(Util.One() + " " + typeof(Util).Name);
    }
}
