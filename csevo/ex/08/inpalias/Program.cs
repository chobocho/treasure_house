// 슬라이드 p8-v7_2-in-alias — in 은 별칭이다, C# 7.2
using System;

class App
{
    static int g;

    static void Show(string how, in int x)
    {
        int before = x;
        g = 42;                     // someone else writes g
        Console.WriteLine(how + ": " + before + " -> " + x);
    }

    static void Main()
    {
        g = 1; Show("in g   ", in g);   // alias of g
        g = 1; Show("g      ", g);      // still the variable g
        g = 1; Show("g + 0  ", g + 0);  // a value: a temp copy
        g = 1; Show("(int)g ", (int)g); // a cast is a value too
    }
}
