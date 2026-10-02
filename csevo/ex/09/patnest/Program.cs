// 슬라이드 p9-v8-proppat-nest — 속성 패턴 안의 속성 패턴, C# 8.0
using System;

class City { public string Name; public int Zone; }
class Customer { public City Home; }
class Order { public Customer Buyer; public int Qty; }

class App
{
    static string Route(Order o) => o switch
    {
        { Buyer: { Home: { Name: "Seoul", Zone: 1 } } } => "same day",
        { Buyer: { Home: { Name: "Seoul" } }, Qty: var q } =>
            "next day x" + q,
        { Buyer: { Home: null } } => "no address",
        { Buyer: { } } => "parcel",
        _ => "no buyer",
    };

    static void Main()
    {
        City s1 = new City { Name = "Seoul", Zone = 1 };
        City s3 = new City { Name = "Seoul", Zone = 3 };
        City bs = new City { Name = "Busan", Zone = 2 };
        Order[] all =
        {
            new Order { Buyer = new Customer { Home = s1 }, Qty = 1 },
            new Order { Buyer = new Customer { Home = s3 }, Qty = 2 },
            new Order { Buyer = new Customer { Home = bs }, Qty = 3 },
            new Order { Buyer = new Customer(), Qty = 4 },
            new Order { Qty = 5 },
        };
        foreach (Order o in all)
            Console.WriteLine(Route(o));
    }
}
