// 슬라이드 p3-v2-alias-qualifier — 별칭 :: 은 별칭만 본다, C# 2.0
using System;
using Col = System.Collections;      // a using alias

namespace Shop
{
    class Col                            // a class with the same name
    {
        public class ArrayList { }
    }

    class App
    {
        static void Main()
        {
            Col.ArrayList a = new Col.ArrayList();      // the class
            Col::ArrayList b = new Col::ArrayList();    // the alias
            Console.WriteLine(a.GetType().FullName);
            Console.WriteLine(b.GetType().FullName);
        }
    }
}
