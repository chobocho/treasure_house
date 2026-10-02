// 슬라이드 p10-v9-tn-where — 대상 형식이 없거나 맞지 않으면, C# 9.0
using System;

enum Color { Red }

class App
{
    static void Main()
    {
        var a = new();                 // no target type
        string s = new().ToString();   // member access
        int n = new() + 1;             // operand of +
        Color c = new(1);              // enum: no constructor
        IDisposable d = new();         // interface
        int[] arr = new();             // array
        dynamic dy = new();            // dynamic
        Action act = new();            // delegate
    }
}
