// 슬라이드 p2-v1-multicast — 여러 메서드를 잇는 대리자, C# 1.0
using System;

delegate void Notify(string msg);

class App
{
    static void ToScreen(string m) { Console.WriteLine("screen " + m); }
    static void ToLog(string m) { Console.WriteLine("log    " + m); }
    static void ToMail(string m) { Console.WriteLine("mail   " + m); }

    static void Main()
    {
        Notify n = new Notify(ToScreen);
        n += new Notify(ToLog);          // Delegate.Combine
        n += new Notify(ToMail);
        n += new Notify(ToLog);          // the same method twice
        n("disk full");
        Console.WriteLine("targets: " + n.GetInvocationList().Length);

        Notify a = new Notify(ToScreen);
        Notify b = a;
        a += new Notify(ToMail);         // a new delegate object
        Console.WriteLine("a: " + a.GetInvocationList().Length
            + ", b: " + b.GetInvocationList().Length);
    }
}
