// 슬라이드 p3-v2-anon-notype — 익명 메서드에는 형식이 없다, C# 2.0
using System;

class App
{
    static void Main()
    {
        object o = delegate { };                 // object: no
        Delegate d = delegate { };               // Delegate: no
        object ok = (EventHandler)delegate { };  // a delegate type: yes
        ok.ToString();
    }
}
