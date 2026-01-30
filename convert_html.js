const fs = require('fs');

const htmlPath = "ClonAfish/Афиша Краснодара 2025-2026 - куда сходить в Краснодаре - мероприятия и события на сегодня, завтра, выходные _ 😋 KASSIR.RU.html";
const pagePath = "web/app/(landing)/page.tsx";
const cardPath = "web/components/MovieCard.tsx";

try {
  let content = fs.readFileSync(htmlPath, 'utf-8');

  // Extract body content
  const bodyStart = content.indexOf("<body");
  const bodyEnd = content.indexOf("</body>");
  let bodyContent = content.substring(content.indexOf(">", bodyStart) + 1, bodyEnd);

  // Remove scripts
  bodyContent = bodyContent.replace(/<script\b[^>]*>([\s\S]*?)<\/script>/gim, "");

  // helper: style string to obj
  const parseStyle = (styleStr) => {
    const styleObj = {};
    styleStr.split(';').forEach(style => {
      const [key, value] = style.split(':');
      if (key && value) {
        const camelKey = key.trim().replace(/-([a-z])/g, (g) => g[1].toUpperCase());
        styleObj[camelKey] = value.trim();
      }
    });
    return JSON.stringify(styleObj);
  };

  // Replace class -> className
  bodyContent = bodyContent.replace(/\sclass="/g, ' className="');

  // Replace style="..." -> style={{...}}
  bodyContent = bodyContent.replace(/\sstyle="([^"]*)"/g, (match, p1) => {
    return ` style={${parseStyle(p1)}}`;
  });

  // Replace void tags
  ['img', 'input', 'br', 'hr', 'source', 'link', 'meta'].forEach(tag => {
    const regex = new RegExp(`<${tag}([^>]*)(?<!/)>`, 'gi');
    bodyContent = bodyContent.replace(regex, `<${tag}$1 />`);
  });

  // Fix specific attributes
  bodyContent = bodyContent.replace(/\sdatetime="/g, ' dateTime="');
  bodyContent = bodyContent.replace(/\ssrcset="/g, ' srcSet="');
  bodyContent = bodyContent.replace(/\sfor="/g, ' htmlFor="');
  bodyContent = bodyContent.replace(/\sfill-rule="/g, ' fillRule="');
  bodyContent = bodyContent.replace(/\sclip-rule="/g, ' clipRule="');
  bodyContent = bodyContent.replace(/\sstroke-width="/g, ' strokeWidth="');
  bodyContent = bodyContent.replace(/\sstroke-linecap="/g, ' strokeLinecap="');
  bodyContent = bodyContent.replace(/\sstroke-linejoin="/g, ' strokeLinejoin="');

  // Comments
  bodyContent = bodyContent.replace(/<!--[\s\S]*?-->/g, '');

  // Identify Movie List Container
  const cardClass = "recommendation-item";
  const startCard = bodyContent.indexOf(cardClass);

  let movieCardHtml = "";
  let pageContent = bodyContent;

  if (startCard !== -1) {
    const ulStart = bodyContent.lastIndexOf("<ul", startCard);
    if (ulStart !== -1) {
      const ulEnd = bodyContent.indexOf("</ul>", ulStart);

      if (ulEnd !== -1) {
        const ulContent = bodyContent.substring(ulStart, ulEnd + 5);

        // Extract the LI that contains the card
        const relStartCard = startCard - ulStart;
        const liStartRelative = ulContent.lastIndexOf("<li", relStartCard);
        const liEndRelative = ulContent.indexOf("</li>", relStartCard);

        if (liStartRelative !== -1 && liEndRelative !== -1) {
          movieCardHtml = ulContent.substring(liStartRelative, liEndRelative + 5);
        } else {
          console.log("Could not find wrapping LI for card");
        }

        const ulTagEnd = bodyContent.indexOf(">", ulStart);
        const ulOpenTag = bodyContent.substring(ulStart, ulTagEnd + 1);

        const replacement = `${ulOpenTag}
                  {movies.map((movie, index) => (
                    <MovieCard key={movie.id || index} movie={movie} />
                  ))}
                </ul>`;

        pageContent = bodyContent.substring(0, ulStart) + replacement + bodyContent.substring(ulEnd + 5);
      }
    }
  }

  // Write Component
  if (movieCardHtml) {
    const componentContent = `
import React from 'react';

export const MovieCard = ({ movie }: { movie: any }) => {
  return (
    ${movieCardHtml}
  );
};
`;
    fs.writeFileSync(cardPath, componentContent, 'utf-8');
    console.log("MovieCard.tsx created (corrected)");
  }

  // Write Page
  const pageTsx = `
"use client";
import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import { MovieCard } from '../../components/MovieCard';
import '../../app/original.css';

export default function LandingPage() {
  const { user } = useAuth();
  const [movies, setMovies] = useState<any[]>([]);

  useEffect(() => {
    api.movies().then(data => {
        if (Array.isArray(data)) setMovies(data);
    }).catch(console.error);
    
    const params = new URLSearchParams(window.location.search);
    const ref = params.get('ref');
    if (ref) {
       api.referral.track(ref);
    }
  }, []);

  return (
    <div className="landing-wrapper">
      ${pageContent}
    </div>
  );
}
`;
  fs.writeFileSync(pagePath, pageTsx, 'utf-8');
  console.log("page.tsx created (corrected)");

} catch (e) {
  console.error(e);
}
