// 슬라이드 p2-v1-namespace — 네임스페이스와 using 별칭, C# 1.0
using System;
using List = System.Collections.ArrayList;     // alias a type
using Drawing = Acme.Graphics.Drawing;         // alias a namespace

namespace Acme.Graphics.Drawing
{
    class Point { public override string ToString() { return "acme"; } }
}

namespace Acme.Mapping
{
    class Point { public override string ToString() { return "map"; } }

    class App
    {
        static void Main()
        {
            Point p = new Point();               // the nearest one wins
            Drawing.Point q = new Drawing.Point();
            List items = new List();
            items.Add(p);
            items.Add(q);
            foreach (object o in items)
                Console.WriteLine(o.GetType().FullName + " -> " + o);
        }
    }
}
